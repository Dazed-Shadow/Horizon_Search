#!/usr/bin/env python3
"""
C-SPOTTER (thin) -- SBA small business finder.

Queries SBA Dynamic Small Business Search (DSBS) for businesses
under the 5 pipeline NAICS codes. Returns {name, naics, url} per
business -- social and financial enrichment deferred to spotter_enrich.py (v0.1).

BLOCKER NOTE (2026-05-26): Both DSBS endpoints (dsbs.sba.gov and
search.certifications.sba.gov) are React SPAs that require JavaScript rendering.
Plain httpx + BeautifulSoup cannot parse them -- there is no fallback JSON API.
This script logs the blocker, writes an empty output file, and exits 0 so the
timing infrastructure still runs end-to-end. Resolution: headless browser (Playwright)
or wait for SBA to publish a public REST API. See DECISIONS.md for next step.

Writes: research/data/candidates/spotter_<YYYY-MM-DD>.jsonl  (may be empty)

Usage:
    python scripts/spotter_find.py
    python scripts/spotter_find.py --limit-per-naics 5
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

HERE           = Path(__file__).resolve().parent.parent   # repo root
CANDIDATES_DIR = HERE / "research" / "data" / "candidates"

sys.path.insert(0, str(HERE / "research"))
from _logs.log_run import log as log_run  # noqa: E402

# Pipeline NAICS -- mirrors fetch_expiring.py / AGENTS.md
PIPELINE_NAICS = {
    "561110": "Office Administrative Services",
    "561990": "All Other Support Services",
    "561320": "Temporary Staffing Services",
    "541611": "Administrative Management Consulting",
    "493110": "General Warehousing & Storage",
}

# SBA DSBS / certifications search endpoints
# Both are React SPAs requiring JS rendering -- plain HTML scrape is not viable.
DSBS_URL  = "https://dsbs.sba.gov/search/dsp_dsbs.cfm"
CERT_URL  = "https://search.certifications.sba.gov/s/search/All"

SPA_MARKER = "<div id=\"root\"></div>"   # fingerprint of JS-only shell page

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _is_spa_shell(html: str) -> bool:
    """Return True if the response is a JS-only SPA shell with no server-rendered data."""
    return SPA_MARKER in html or len(BeautifulSoup(html, "html.parser").get_text(strip=True)) < 100


def search_dsbs(client: httpx.Client, naics: str, limit: int) -> tuple[list[dict], list[str]]:
    """
    Attempt to query DSBS for a single NAICS code.
    Returns (records, errors).
    """
    errors:  list[str]  = []
    records: list[dict] = []

    params = {
        "SB_SIZE":       "S",
        "NAICS_CODE":    naics,
        "ROWS":          str(limit),
        "START_ROW":     "1",
        "DB_SORT_ORDER": "LEGALNAME",
        "DB_SORT_DIR":   "ASC",
    }

    try:
        resp = client.get(DSBS_URL, params=params, headers=HEADERS, timeout=30)

        if resp.status_code != 200:
            errors.append(f"DSBS returned HTTP {resp.status_code} for NAICS {naics}")
            return records, errors

        if _is_spa_shell(resp.text):
            errors.append(
                f"BLOCKER: DSBS is a React SPA -- requires JS rendering (Playwright). "
                f"NAICS {naics} returned no server-rendered data."
            )
            return records, errors

        # If we ever get real HTML (e.g. SBA re-enables server rendering), parse it.
        soup = BeautifulSoup(resp.text, "html.parser")
        seen: set[str] = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "dsp_profile.cfm" in href or "dsp_dsbs_detail" in href:
                name = a_tag.get_text(strip=True)
                if not name or name in seen:
                    continue
                seen.add(name)
                full_url = href if href.startswith("http") else "https://dsbs.sba.gov" + href
                records.append({"name": name, "naics": naics, "url": full_url})
                if len(records) >= limit:
                    break

        if not records:
            errors.append(f"DSBS: page returned HTML but no profile links for NAICS {naics}")

    except httpx.TimeoutException:
        errors.append(f"DSBS timeout for NAICS {naics}")
    except Exception as exc:
        errors.append(f"DSBS error for NAICS {naics}: {exc}")

    return records, errors


def write_candidates(records: list[dict]) -> Path:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = CANDIDATES_DIR / f"spotter_{date_str}.jsonl"

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="C-SPOTTER: find SBA small businesses by NAICS")
    parser.add_argument(
        "--limit-per-naics", type=int, default=10,
        help="Max businesses per NAICS code (default: 10)",
    )
    args = parser.parse_args()

    started_at  = datetime.now(timezone.utc)
    all_records: list[dict] = []
    all_errors:  list[str]  = []

    print(f"C-SPOTTER: querying DSBS for {len(PIPELINE_NAICS)} NAICS codes "
          f"(limit {args.limit_per_naics}/code)")

    with httpx.Client(follow_redirects=True) as client:
        for i, (naics, label) in enumerate(PIPELINE_NAICS.items(), 1):
            print(f"  [{i}/{len(PIPELINE_NAICS)}] {naics} -- {label}")
            records, errors = search_dsbs(client, naics, args.limit_per_naics)
            all_records.extend(records)
            all_errors.extend(errors)
            status_str = f"{len(records)} businesses" if records else "0 (see errors)"
            print(f"    {status_str}")
            if errors:
                for e in errors:
                    print(f"    [WARN] {e}")

    out_path = write_candidates(all_records)
    print(f"\nTotal: {len(all_records)} candidates -> {out_path}")
    if not all_records:
        print("[INFO] Empty output -- DSBS SPA wall. See script header for resolution path.")

    log_run("c-spotter", started_at, record_count=len(all_records),
            errors=all_errors if all_errors else None)


if __name__ == "__main__":
    main()
