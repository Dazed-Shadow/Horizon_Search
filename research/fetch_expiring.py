#!/usr/bin/env python3
"""
C-MainLiner -- SAM.gov expiring contracts fetcher.

Sibling to fetch_awards.py. Pulls opportunities (ptype=o) where
responseDeadLine falls within the next 28 days, filtered to pipeline NAICS codes.

Writes: research/data/contracts/expiring_<YYYY-MM-DD>.json

Usage (from repo root OR research/ dir):
    python research/fetch_expiring.py              # all 5 pipeline NAICS codes
    python research/fetch_expiring.py 561110       # single code
    python research/fetch_expiring.py 561110 561990 # multiple codes
    python research/fetch_expiring.py --focus      # same flag as fetch_awards.py
    python research/fetch_expiring.py --delay 2.0  # slower if 429s

Requirements: httpx (already installed via backend venv)
API key: read from backend/.env automatically
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Paths -- mirrors fetch_awards.py conventions
# ---------------------------------------------------------------------------
HERE          = Path(__file__).resolve().parent
DATA_DIR      = HERE / "data"
CONTRACTS_DIR = DATA_DIR / "contracts"
ENV_PATH      = HERE.parent / "backend" / ".env"
SAM_BASE      = "https://api.sam.gov/opportunities/v2/search"

sys.path.insert(0, str(HERE))
from _logs.log_run import log as log_run  # noqa: E402

# ---------------------------------------------------------------------------
# Pipeline NAICS set -- single source of truth for this prototype
# ---------------------------------------------------------------------------
PIPELINE_NAICS = {
    "561110": "Office Administrative Services",
    "561990": "All Other Support Services",
    "561320": "Temporary Staffing Services",
    "541611": "Administrative Management Consulting",
    "493110": "General Warehousing & Storage",
}

# ---------------------------------------------------------------------------
# Env loading -- copied from fetch_awards.py idiom
# ---------------------------------------------------------------------------
def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# ---------------------------------------------------------------------------
# SAM.gov fetch -- one page, opportunity notices (ptype=o)
# ---------------------------------------------------------------------------
def fetch_page(
    client: httpx.Client,
    api_key: str,
    naics: str,
    posted_from: str,
    posted_to: str,
    offset: int = 0,
    page_size: int = 100,
) -> dict:
    params = {
        "api_key":    api_key,
        "ptype":      "o",           # Presolicitation / opportunity notices
        "naicsCode":  naics,
        "postedFrom": posted_from,
        "postedTo":   posted_to,
        "limit":      page_size,
        "offset":     offset,
    }
    resp = client.get(SAM_BASE, params=params, timeout=45)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Check if an opportunity's responseDeadLine is within the window
# ---------------------------------------------------------------------------
def deadline_in_window(opp: dict, from_dt: datetime, to_dt: datetime) -> bool:
    deadline_str = opp.get("responseDeadLine") or ""
    if not deadline_str:
        return False
    try:
        # SAM.gov returns e.g. "2026-06-15T23:59:00-05:00"
        dl = datetime.fromisoformat(deadline_str)
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        from_utc = from_dt.replace(tzinfo=timezone.utc) if from_dt.tzinfo is None else from_dt
        to_utc   = to_dt.replace(tzinfo=timezone.utc) if to_dt.tzinfo is None else to_dt
        return from_utc <= dl <= to_utc
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Parse opportunity -> flat dict (mirrors fetch_awards.py shape)
# ---------------------------------------------------------------------------
def parse_opportunity(opp: dict, naics: str) -> dict | None:
    try:
        pop = opp.get("placeOfPerformance") or {}
        if isinstance(pop, dict):
            city  = (pop.get("city")  or {}).get("name", "") or ""
            state = (pop.get("state") or {}).get("code", "") or ""
        else:
            city, state = "", str(pop or "")

        sa_code = opp.get("typeOfSetAside") or ""

        return {
            "notice_id":       opp.get("noticeId", ""),
            "title":           opp.get("title", ""),
            "naics_code":      naics,
            "naics_label":     PIPELINE_NAICS.get(naics, naics),
            "posted_date":     opp.get("postedDate", ""),
            "response_deadline": opp.get("responseDeadLine", ""),
            "agency":          (
                opp.get("fullParentPathName")
                or opp.get("department")
                or opp.get("organizationName")
                or ""
            ),
            "city":            city.strip().title(),
            "state":           state.strip().upper(),
            "set_aside_code":  sa_code,
            "ui_link":         opp.get("uiLink", ""),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Fetch and filter for one NAICS code
# ---------------------------------------------------------------------------
def fetch_expiring_for_naics(
    client: httpx.Client,
    api_key: str,
    naics: str,
    window_from: datetime,
    window_to: datetime,
    search_from: str,
    search_to: str,
    delay: float,
) -> tuple[list[dict], list[str]]:
    """
    Fetch recent opportunity notices for a NAICS code and post-filter
    to those whose responseDeadLine is within [window_from, window_to].
    Returns (matches, errors).
    """
    matches: list[dict] = []
    errors:  list[str]  = []
    offset   = 0
    page_sz  = 100
    total_known: int | None = None

    retry_count = 0
    max_retries = 3

    while True:
        try:
            data = fetch_page(client, api_key, naics, search_from, search_to, offset, page_sz)
            retry_count = 0  # reset on success
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_count += 1
                if retry_count > max_retries:
                    msg = f"NAICS {naics}: SAM.gov 429 -- max retries ({max_retries}) exceeded"
                    errors.append(msg)
                    print(f"  [429] {msg}")
                    break
                print(f"  [429] Rate limited -- waiting 60s (retry {retry_count}/{max_retries}) ...")
                time.sleep(60)
                continue
            msg = f"NAICS {naics}: HTTP {e.response.status_code}"
            errors.append(msg)
            print(f"  [{msg}] skipping")
            break
        except (httpx.TimeoutException, Exception) as e:
            msg = f"NAICS {naics}: {e}"
            errors.append(msg)
            print(f"  [ERROR] {msg}")
            break

        opps = data.get("opportunitiesData") or []
        if total_known is None:
            try:
                total_known = int(data.get("totalRecords", 0))
            except (ValueError, TypeError):
                total_known = 0

        for opp in opps:
            if deadline_in_window(opp, window_from, window_to):
                parsed = parse_opportunity(opp, naics)
                if parsed:
                    matches.append(parsed)

        offset += len(opps)
        if not opps or offset >= (total_known or 0) or offset >= 10_000:
            break

        time.sleep(delay)

    return matches, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="C-MainLiner: fetch SAM.gov contracts expiring in the next 28 days"
    )
    parser.add_argument(
        "codes", nargs="*",
        help="NAICS codes to fetch (default: all 5 pipeline codes)",
    )
    parser.add_argument(
        "--focus", action="store_true",
        help="Use all 5 pipeline NAICS codes (same as default -- flag kept for CLI parity)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Seconds between API calls (default: 1.5)",
    )
    parser.add_argument(
        "--window-days", type=int, default=28,
        help="Days ahead to include in expiring window (default: 28)",
    )
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    api_key = env.get("SAM_GOV_API_KEY") or os.getenv("SAM_GOV_API_KEY", "")
    if not api_key:
        print(f"ERROR: SAM_GOV_API_KEY not found in {ENV_PATH}")
        sys.exit(1)

    target_codes = args.codes if args.codes else list(PIPELINE_NAICS.keys())

    now        = datetime.now(timezone.utc)
    win_from   = now
    win_to     = now + timedelta(days=args.window_days)
    # SAM search window: posted in the last 90 days to catch anything with upcoming deadlines
    search_from_dt = now - timedelta(days=90)
    search_to_dt   = now
    fmt = "%m/%d/%Y"
    search_from = search_from_dt.strftime(fmt)
    search_to   = search_to_dt.strftime(fmt)

    print(f"\nC-MainLiner -- SAM.gov Expiring Contracts")
    print(f"Deadline window : now -> +{args.window_days} days ({win_to.strftime('%Y-%m-%d')})")
    print(f"Search posted   : {search_from} -> {search_to}")
    print(f"NAICS codes     : {', '.join(target_codes)}\n")

    started_at = datetime.now(timezone.utc)
    all_matches: list[dict] = []
    errors: list[str] = []

    with httpx.Client() as client:
        for i, naics in enumerate(target_codes, 1):
            label = PIPELINE_NAICS.get(naics, naics)
            print(f"[{i}/{len(target_codes)}] {naics} -- {label}")
            try:
                matches, errs = fetch_expiring_for_naics(
                    client, api_key, naics,
                    win_from, win_to, search_from, search_to, args.delay,
                )
                all_matches.extend(matches)
                errors.extend(errs)
                print(f"  {len(matches)} expiring contracts found")
            except Exception as exc:
                msg = f"NAICS {naics}: {exc}"
                errors.append(msg)
                print(f"  [ERROR] {msg}")

            if i < len(target_codes):
                time.sleep(args.delay)

    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str  = now.strftime("%Y-%m-%d")
    out_path  = CONTRACTS_DIR / f"expiring_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=2, ensure_ascii=False)

    print(f"\nTotal expiring: {len(all_matches)} contracts -> {out_path}")
    log_run("c-mainliner", started_at, record_count=len(all_matches), errors=errors or None)


if __name__ == "__main__":
    main()
