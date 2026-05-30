#!/usr/bin/env python3
"""
C-SPOTTER-AWARDS -- USAspending.gov award history enrichment.

Reads a spotter_<YYYY-MM-DD>.jsonl candidate file (produced by spotter_find.py),
looks up each business's federal award history on USAspending.gov, and writes a
sidecar file:

  research/data/candidates/spotter_<date>_awards.jsonl

The original JSONL is never modified (canonical raw scrape). The sidecar adds
three award fields per record:

  first_award    -- earliest prime contract by Start Date:
                    {date, amount, agency, description, contract_type, award_id}
  latest_award   -- most recent prime contract by Start Date (same shape)
  total_awards_count  -- integer
  award_status   -- one of:
                    "has_awards"              → at least one prime contract found
                    "no_federal_awards_found" → query succeeded but zero results
                    "lookup_failed"           → network/parse error; first/latest are null

spotter_package.py prefers the awards sidecar if it exists for the requested
date; falls back to the plain spotter_<date>.jsonl if not.

## Why USAspending, not SAM.gov

JR's standing API-budget rule (see D-015 Phase 2, DECISIONS.md): reserve the
HZ SAM_GOV_API_KEY for user-facing flows. USAspending is a separate public API
with no key requirement and indexes federal awards by recipient UEI -- which we
already carry in sam_profile_url.

## USAspending field mapping (confirmed against live API 2026-05-30)

  "Award ID"          → award_id  (contract number / PIID-equivalent)
  "Start Date"        → date      (action date, ISO string "YYYY-MM-DD")
  "Award Amount"      → amount    (float, USD)
  "Awarding Agency"   → agency    (string, e.g. "Department of Defense")
  "Description"       → description
  "Contract Award Type" → contract_type (e.g. "PURCHASE ORDER")

  Note: the API-native "piid" field was null in all tested responses; "Award ID"
  is the usable contract-number field. "Award Type" was also null for every
  tested contract record; "Contract Award Type" is the correct field.

## Annotation preservation (spotter_package.py)

This script does not touch annotations. The annotation-preservation logic
(CAGE-keyed carry-forward of jr_status/jr_notes/jr_priority) lives entirely in
spotter_package.py -- see D-021.

Usage:
    python scripts/spotter_awards.py
    python scripts/spotter_awards.py --date 2026-05-29
    python scripts/spotter_awards.py --date 2026-05-29 --limit 3
    python scripts/spotter_awards.py --delay-seconds 0.5
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

HERE           = Path(__file__).resolve().parent.parent  # repo root
CANDIDATES_DIR = HERE / "research" / "data" / "candidates"

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USASPENDING_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

# UEI extracted from sam_profile_url like:
#   https://sam.gov/entity/H26KNRBSEX89/coreData?...
UEI_RE = re.compile(r"/entity/([A-Z0-9]{12})/")

# Request fields we care about (confirmed available in the API)
AWARD_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Award Amount",
    "Awarding Agency",
    "Award Type",
    "Start Date",
    "Description",
    "Contract Award Type",
]

# Contract-only award type codes (exclude grants, loans, direct payments)
CONTRACT_AWARD_TYPE_CODES = ["A", "B", "C", "D"]

DEFAULT_DELAY = 0.75
REQUEST_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# USAspending helpers
# ---------------------------------------------------------------------------

def _extract_uei(sam_profile_url: str | None) -> str | None:
    """Parse the 12-char UEI from a sam.gov entity URL. Returns None if not found."""
    if not sam_profile_url:
        return None
    m = UEI_RE.search(sam_profile_url)
    return m.group(1) if m else None


def _make_award_obj(result: dict) -> dict:
    """Convert one USAspending result dict to our normalized award object."""
    return {
        "date":          result.get("Start Date"),
        "amount":        result.get("Award Amount"),
        "agency":        result.get("Awarding Agency"),
        "description":   result.get("Description"),
        "contract_type": result.get("Contract Award Type"),
        "award_id":      result.get("Award ID"),
    }


def _query_awards(uei: str, client: httpx.Client) -> tuple[str, dict | None, dict | None, int]:
    """
    Query USAspending for all prime contracts awarded to the given UEI.

    Returns:
        (award_status, first_award, latest_award, total_count)

    award_status is one of:
        "has_awards"              -- at least one result
        "no_federal_awards_found" -- query ok, zero results
        "lookup_failed"           -- network / parse error
    """
    base_payload = {
        "filters": {
            "recipient_search_text": [uei],
            "award_type_codes": CONTRACT_AWARD_TYPE_CODES,
        },
        "fields": AWARD_FIELDS,
        "limit": 100,
        "subawards": False,
    }

    try:
        # Ascending pass: get first (earliest) award
        asc_payload = {**base_payload, "sort": "Start Date", "order": "asc", "page": 1}
        r_asc = client.post(USASPENDING_URL, json=asc_payload, timeout=REQUEST_TIMEOUT)
        r_asc.raise_for_status()
        data_asc = r_asc.json()
        results = data_asc.get("results", [])

        if not results:
            return "no_federal_awards_found", None, None, 0

        first_award = _make_award_obj(results[0])

        # If only one result, first == latest
        if len(results) == 1 and not data_asc["page_metadata"]["hasNext"]:
            return "has_awards", first_award, first_award, 1

        # Descending pass: get latest award (page 1 desc = most recent)
        desc_payload = {**base_payload, "sort": "Start Date", "order": "desc", "page": 1}
        r_desc = client.post(USASPENDING_URL, json=desc_payload, timeout=REQUEST_TIMEOUT)
        r_desc.raise_for_status()
        data_desc = r_desc.json()
        results_desc = data_desc.get("results", [])
        latest_award = _make_award_obj(results_desc[0]) if results_desc else first_award

        # Total count: if no pagination, len(results) is the total.
        # USAspending doesn't return a total count in this endpoint; we use
        # the result set size. If hasNext is True, we know there are >100;
        # we report what we have without fetching all pages (bounded effort).
        has_next = data_asc["page_metadata"].get("hasNext", False)
        total_count = len(results) if not has_next else f"{len(results)}+"
        # Normalize to int for JSON compatibility (treat "N+" as N for now)
        if isinstance(total_count, str):
            total_count = int(total_count.rstrip("+"))

        return "has_awards", first_award, latest_award, total_count

    except (httpx.HTTPStatusError, httpx.RequestError, KeyError, ValueError) as exc:
        return "lookup_failed", None, None, 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="C-SPOTTER-AWARDS: enrich candidate JSONL with USAspending.gov award history"
    )
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        metavar="YYYY-MM-DD",
        help="Date of the spotter JSONL to enrich (default: today)",
    )
    parser.add_argument(
        "--delay-seconds", type=float, default=DEFAULT_DELAY,
        metavar="F",
        help=f"Polite delay between USAspending queries in seconds (default: {DEFAULT_DELAY})",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        metavar="N",
        help="Process only the first N records (default: all; useful for testing)",
    )
    args = parser.parse_args()

    date_str   = args.date
    delay      = args.delay_seconds
    limit      = args.limit

    in_path  = CANDIDATES_DIR / f"spotter_{date_str}.jsonl"
    out_path = CANDIDATES_DIR / f"spotter_{date_str}_awards.jsonl"

    if not in_path.exists():
        print(f"[ERROR] Input file not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    # Load records
    records: list[dict] = []
    with open(in_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"[WARN] Line {lineno} is not valid JSON — skipping: {exc}", file=sys.stderr)

    if limit is not None:
        records = records[:limit]

    print(
        f"C-SPOTTER-AWARDS: enriching {len(records)} record(s) from {in_path.name} "
        f"(delay {delay}s between queries)"
    )

    started_at = datetime.now(timezone.utc)
    enriched: list[dict] = []
    errors: list[str] = []

    with httpx.Client() as client:
        for i, rec in enumerate(records, 1):
            name = rec.get("name", f"record #{i}")
            sam_url = rec.get("sam_profile_url")
            uei = _extract_uei(sam_url)

            if not uei:
                msg = f"[{i}/{len(records)}] {name[:55]}: no UEI in sam_profile_url — skipping"
                print(f"  {msg}")
                errors.append(msg)
                out_rec = dict(rec)
                out_rec["award_status"]       = "lookup_failed"
                out_rec["first_award"]        = None
                out_rec["latest_award"]       = None
                out_rec["total_awards_count"] = 0
                enriched.append(out_rec)
                continue

            award_status, first_award, latest_award, total_count = _query_awards(uei, client)

            if award_status == "lookup_failed":
                msg = f"[{i}/{len(records)}] {name[:55]}: lookup_failed (UEI={uei})"
                print(f"  {msg}")
                errors.append(msg)
            elif award_status == "no_federal_awards_found":
                print(f"  [{i}/{len(records)}] {name[:55]}: no_federal_awards_found")
            else:
                fa = first_award or {}
                la = latest_award or {}
                print(
                    f"  [{i}/{len(records)}] {name[:55]}: has_awards "
                    f"({total_count} contract(s)) "
                    f"first={fa.get('date')} ${fa.get('amount', 0):,.0f} "
                    f"latest={la.get('date')} ${la.get('amount', 0):,.0f}"
                )

            out_rec = dict(rec)
            out_rec["award_status"]       = award_status
            out_rec["first_award"]        = first_award
            out_rec["latest_award"]       = latest_award
            out_rec["total_awards_count"] = total_count
            enriched.append(out_rec)

            if i < len(records):
                time.sleep(delay)

    # Write sidecar
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in enriched:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    has_awards_count = sum(1 for r in enriched if r.get("award_status") == "has_awards")
    no_awards_count  = sum(1 for r in enriched if r.get("award_status") == "no_federal_awards_found")
    failed_count     = sum(1 for r in enriched if r.get("award_status") == "lookup_failed")
    print(
        f"\nC-SPOTTER-AWARDS: done. "
        f"{has_awards_count} has_awards / {no_awards_count} no_federal_awards_found / "
        f"{failed_count} lookup_failed"
    )
    print(f"  Sidecar -> {out_path}  ({out_path.stat().st_size:,} bytes)")

    log_run(
        "c-spotter-awards",
        started_at,
        record_count=len(enriched),
        errors=errors if errors else None,
    )


if __name__ == "__main__":
    main()
