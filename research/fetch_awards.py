#!/usr/bin/env python3
"""
SAM.gov Award Notice downloader — local research tool.

Pulls Award Notices (ptype=a) for the past 24 months by NAICS code,
then writes three CSVs for outreach planning:

  data/awards_raw.csv       — one row per award notice
  data/awards_by_city.csv   — NAICS × city × state: count + total $
  data/awards_by_agency.csv — agency × NAICS: count + total $ + city breakdown

Usage (run from repo root OR research/ dir):
  python research/fetch_awards.py --focus              # curated 10 high-activity codes
  python research/fetch_awards.py 541512               # single code
  python research/fetch_awards.py 541512 541519        # multiple codes
  python research/fetch_awards.py --focus --resume     # pick up after a timeout
  python research/fetch_awards.py --delay 2.0          # slower (if hitting 429s)
  python research/fetch_awards.py --months 12          # shorter lookback

Requirements: httpx (already installed via backend venv)
API key: read from backend/.env automatically
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE     = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ENV_PATH = HERE.parent / "backend" / ".env"
SAM_BASE = "https://api.sam.gov/opportunities/v2/search"

PROGRESS_FILE = DATA_DIR / ".progress.json"
RAW_CSV       = DATA_DIR / "awards_raw.csv"
CITY_CSV      = DATA_DIR / "awards_by_city.csv"
AGENCY_CSV    = DATA_DIR / "awards_by_agency.csv"

# ---------------------------------------------------------------------------
# NAICS codes — mirrors COMMON_NAICS in frontend/src/utils/constants.js
# ---------------------------------------------------------------------------
NAICS_CODES = {
    # Construction
    "236115": "New Single-Family Housing Construction",
    "236220": "Commercial & Institutional Building Construction",
    "237110": "Water & Sewer Line Construction",
    "237310": "Highway, Street, and Bridge Construction",
    "237990": "Other Heavy & Civil Engineering Construction",
    "238110": "Poured Concrete Foundation & Structure Work",
    "238990": "All Other Specialty Trade Contractors",
    # Technology & IT
    "511210": "Software Publishers",
    "517110": "Wired Telecommunications Carriers",
    "517410": "Satellite Telecommunications",
    "518210": "Data Processing & Hosting",
    "519290": "Web Search Portals & Other Info Services",
    "541511": "Custom Computer Programming Services",
    "541512": "Computer Systems Design Services",
    "541513": "Computer Facilities Management Services",
    "541519": "Other Computer Related Services",
    "811212": "Computer & Office Machine Repair & Maintenance",
    # Professional & Consulting
    "541211": "Offices of Certified Public Accountants",
    "541310": "Architectural Services",
    "541330": "Engineering Services",
    "541380": "Testing Laboratories & Services",
    "541611": "Administrative Management Consulting",
    "541612": "Human Resources Consulting",
    "541613": "Marketing Consulting Services",
    "541620": "Environmental Consulting Services",
    "541690": "Other Scientific & Technical Consulting",
    "541711": "R&D in Biotechnology",
    "541715": "R&D in Physical & Engineering Sciences",
    "541990": "All Other Professional & Scientific Services",
    # Administrative & Support
    "561110": "Office Administrative Services",
    "561210": "Facilities Support Services",
    "561320": "Temporary Staffing Services",
    "561612": "Security Guard & Patrol Services",
    "561621": "Security Systems Services",
    "561720": "Janitorial Services",
    "561730": "Landscaping Services",
    "561990": "All Other Support Services",
    # Healthcare & Medical
    "621111": "Offices of Physicians",
    "621330": "Offices of Mental Health Practitioners",
    "621399": "Offices of All Other Health Practitioners",
    "621610": "Home Health Care Services",
    "621910": "Ambulance Services",
    "622110": "General Medical & Surgical Hospitals",
    "623110": "Nursing Care Facilities",
    # Defense & Aerospace
    "336411": "Aircraft Manufacturing",
    "336413": "Other Aircraft Parts & Equipment Manufacturing",
    "336992": "Military Armored Vehicle Manufacturing",
    "488190": "Other Support Activities for Air Transportation",
    "811310": "Commercial & Industrial Machinery Repair",
    # Logistics & Transportation
    "484110": "General Freight Trucking, Local",
    "484121": "General Freight Trucking, Long-Distance",
    "488510": "Freight Transportation Arrangement",
    "493110": "General Warehousing & Storage",
    "532490": "Other Commercial & Industrial Equipment Rental",
}

# Curated 10 codes — highest federal award volume + veteran set-aside activity.
# Covers IT, consulting, facilities, healthcare, and logistics for diversity.
FOCUS_CODES = [
    "541512",  # Computer Systems Design — cloud, IT infra, systems integration
    "541511",  # Custom Computer Programming — software dev, DevSecOps, app modernization
    "541611",  # Administrative Management Consulting — program mgmt, strategic planning
    "541330",  # Engineering Services — civil/mechanical/systems for DoD facilities
    "561210",  # Facilities Support Services — base ops, maintenance for military installations
    "561720",  # Janitorial Services — federal buildings, highest SDVOSB set-aside rate
    "561612",  # Security Guard & Patrol — uniformed guards for federal buildings/bases
    "621610",  # Home Health Care Services — VA community care, nursing/aide contracts
    "541690",  # Other Scientific & Technical Consulting — EPA/DOE advisory, env science
    "484110",  # General Freight Trucking Local — military supply chain delivery
]

SET_ASIDE_LABELS = {
    "SBA":      "Small Business",
    "SBP":      "Small Business (Partial)",
    "8A":       "8(a) Sole Source",
    "8AN":      "8(a) Competitive",
    "HZC":      "HUBZone Set-Aside",
    "HZS":      "HUBZone Sole Source",
    "SDVOSBC":  "SDVOSB Competitive",
    "SDVOSBS":  "SDVOSB Sole Source",
    "WOSB":     "WOSB Set-Aside",
    "WOSBSS":   "WOSB Sole Source",
    "EDWOSB":   "EDWOSB Set-Aside",
    "EDWOSBSS": "EDWOSB Sole Source",
    "VSB":      "Veteran-Owned Small Business",
    "VOSB":     "Veteran-Owned Small Business",
    "IEE":      "Indian Economic Enterprise",
    "ISBEE":    "Indian Small Business Economic Enterprise",
    "A":        "Total Small Business",
}

VETERAN_CODES = {"SDVOSBC", "SDVOSBS", "VSB", "VOSB"}

RAW_FIELDS = [
    "notice_id", "posted_date", "naics_code", "naics_label",
    "city", "state", "agency", "sub_agency", "office",
    "awardee", "award_amount", "set_aside_code", "set_aside_label",
    "is_veteran", "title", "ui_link",
]


# ---------------------------------------------------------------------------
# Env loading
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
# Progress tracking — lets --resume skip already-completed codes
# ---------------------------------------------------------------------------
def load_progress() -> set[str]:
    if PROGRESS_FILE.exists():
        try:
            return set(json.loads(PROGRESS_FILE.read_text()).get("done", []))
        except Exception:
            pass
    return set()


def save_progress(done: set[str]) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps({"done": sorted(done)}, indent=2))


def clear_progress() -> None:
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()


# ---------------------------------------------------------------------------
# Incremental CSV append — write each code's rows immediately after fetch
# ---------------------------------------------------------------------------
def append_raw_csv(rows: list[dict]) -> None:
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not RAW_CSV.exists()
    with open(RAW_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def read_all_raw() -> list[dict]:
    if not RAW_CSV.exists():
        return []
    with open(RAW_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# SAM.gov fetch — single page
# ---------------------------------------------------------------------------
def fetch_page(
    client: httpx.Client,
    api_key: str,
    naics: str,
    posted_from: str,
    posted_to: str,
    offset: int = 0,
    page_size: int = 1000,
) -> dict:
    params = {
        "api_key":    api_key,
        "ptype":      "a",
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
# Parse opportunity → flat dict
# ---------------------------------------------------------------------------
def parse_opportunity(opp: dict, naics: str) -> dict | None:
    try:
        pop = opp.get("placeOfPerformance") or {}
        if isinstance(pop, dict):
            city  = (pop.get("city")  or {}).get("name", "") or ""
            state = (pop.get("state") or {}).get("code", "") or ""
        else:
            city, state = "", str(pop or "")

        award      = opp.get("award") or {}
        awardee    = award.get("awardee") or {}
        awardee_nm = awardee.get("name") or awardee.get("legalBusinessName") or ""
        try:
            amount = float(award.get("amount") or 0) or None
        except (ValueError, TypeError):
            amount = None

        sa_code = opp.get("typeOfSetAside") or ""

        return {
            "notice_id":       opp.get("noticeId", ""),
            "title":           opp.get("title", ""),
            "naics_code":      naics,
            "naics_label":     NAICS_CODES.get(naics, naics),
            "posted_date":     opp.get("postedDate", ""),
            "agency":          (
                opp.get("fullParentPathName")
                or opp.get("department")
                or opp.get("organizationName")
                or ""
            ),
            "sub_agency":      opp.get("subtier", ""),
            "office":          opp.get("office", ""),
            "city":            city.strip().title(),
            "state":           state.strip().upper(),
            "awardee":         awardee_nm.strip(),
            "award_amount":    amount,
            "set_aside_code":  sa_code,
            "set_aside_label": SET_ASIDE_LABELS.get(sa_code, sa_code),
            "is_veteran":      sa_code in VETERAN_CODES,
            "ui_link":         opp.get("uiLink", ""),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Date chunking — SAM.gov free tier rejects spans > 365 days
# ---------------------------------------------------------------------------
MAX_WINDOW_DAYS = 365


def date_chunks(from_dt: datetime, to_dt: datetime) -> list[tuple[str, str]]:
    fmt = "%m/%d/%Y"
    chunks = []
    chunk_end = to_dt
    while chunk_end > from_dt:
        chunk_start = max(from_dt, chunk_end - timedelta(days=MAX_WINDOW_DAYS))
        chunks.append((chunk_start.strftime(fmt), chunk_end.strftime(fmt)))
        chunk_end = chunk_start - timedelta(days=1)
    return chunks


# ---------------------------------------------------------------------------
# Fetch one date window, auto-paginate
# ---------------------------------------------------------------------------
def fetch_window(
    client: httpx.Client,
    api_key: str,
    naics: str,
    posted_from: str,
    posted_to: str,
    delay: float,
) -> list[dict]:
    rows = []
    offset = 0
    total_known = None

    while True:
        try:
            data = fetch_page(client, api_key, naics, posted_from, posted_to, offset)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print("  [429] Rate limited — waiting 60s …")
                time.sleep(60)
                continue
            print(f"  [HTTP {e.response.status_code}]")
            break
        except httpx.TimeoutException:
            print("  [TIMEOUT] — skipping this window")
            break
        except Exception as e:
            print(f"  [ERROR] {e}")
            break

        opps = data.get("opportunitiesData") or []
        if total_known is None:
            try:
                total_known = int(data.get("totalRecords", 0))
            except (ValueError, TypeError):
                total_known = 0

        for opp in opps:
            row = parse_opportunity(opp, naics)
            if row:
                rows.append(row)

        offset += len(opps)
        if not opps or offset >= total_known or offset >= 10_000:
            break

        time.sleep(delay)

    return rows


# ---------------------------------------------------------------------------
# Fetch all windows for one NAICS code, deduplicate
# ---------------------------------------------------------------------------
def fetch_all_for_naics(
    client: httpx.Client,
    api_key: str,
    naics: str,
    from_dt: datetime,
    to_dt: datetime,
    delay: float,
) -> list[dict]:
    chunks = date_chunks(from_dt, to_dt)
    seen: set[str] = set()
    all_rows: list[dict] = []

    for idx, (pf, pt) in enumerate(chunks, 1):
        print(f"  [window {idx}/{len(chunks)}: {pf} → {pt}]", end=" ", flush=True)
        rows = fetch_window(client, api_key, naics, pf, pt, delay)
        new = [r for r in rows if r["notice_id"] not in seen]
        for r in new:
            seen.add(r["notice_id"])
        all_rows.extend(new)
        print(f"{len(new):,} awards  (total: {len(all_rows):,})")
        if idx < len(chunks):
            time.sleep(delay)

    return all_rows


# ---------------------------------------------------------------------------
# Summary builders
# ---------------------------------------------------------------------------
def build_city_summary(rows: list[dict]) -> list[dict]:
    bucket: dict[tuple, dict] = defaultdict(lambda: {
        "count": 0, "total_amount": 0.0, "veteran_count": 0, "agencies": set(),
    })
    for r in rows:
        key = (r["naics_code"], r["naics_label"], r["city"], r["state"])
        b = bucket[key]
        b["count"] += 1
        try:
            b["total_amount"] += float(r["award_amount"] or 0)
        except (ValueError, TypeError):
            pass
        if str(r.get("is_veteran", "")).lower() in ("true", "1"):
            b["veteran_count"] += 1
        ag = str(r.get("agency", "")).split("|")[0].strip()
        if ag:
            b["agencies"].add(ag)

    summary = []
    for (naics, label, city, state), b in bucket.items():
        summary.append({
            "naics_code":     naics,
            "naics_label":    label,
            "city":           city,
            "state":          state,
            "award_count":    b["count"],
            "total_dollars":  round(b["total_amount"]),
            "avg_dollars":    round(b["total_amount"] / b["count"]) if b["count"] else 0,
            "veteran_awards": b["veteran_count"],
            "top_agencies":   " | ".join(sorted(b["agencies"])[:5]),
        })
    return sorted(summary, key=lambda x: x["total_dollars"], reverse=True)


def build_agency_summary(rows: list[dict]) -> list[dict]:
    bucket: dict[tuple, dict] = defaultdict(lambda: {
        "count": 0, "total_amount": 0.0, "veteran_count": 0,
        "cities": defaultdict(int),
    })
    for r in rows:
        agency = str(r.get("agency", "")).split("|")[0].strip() or "Unknown"
        key = (agency, r["naics_code"], r["naics_label"])
        b = bucket[key]
        b["count"] += 1
        try:
            b["total_amount"] += float(r["award_amount"] or 0)
        except (ValueError, TypeError):
            pass
        if str(r.get("is_veteran", "")).lower() in ("true", "1"):
            b["veteran_count"] += 1
        loc = f"{r['city']}, {r['state']}" if r.get("city") else r.get("state", "")
        if loc.strip(", "):
            b["cities"][loc] += 1

    summary = []
    for (agency, naics, label), b in bucket.items():
        top_cities = sorted(b["cities"].items(), key=lambda x: x[1], reverse=True)[:5]
        summary.append({
            "agency":         agency,
            "naics_code":     naics,
            "naics_label":    label,
            "award_count":    b["count"],
            "total_dollars":  round(b["total_amount"]),
            "avg_dollars":    round(b["total_amount"] / b["count"]) if b["count"] else 0,
            "veteran_awards": b["veteran_count"],
            "top_cities":     " | ".join(f"{c} ({n})" for c, n in top_cities),
        })
    return sorted(summary, key=lambda x: x["total_dollars"], reverse=True)


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------
def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows → {path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SAM.gov award notices by NAICS code")
    parser.add_argument(
        "codes", nargs="*",
        help="NAICS codes to fetch (omit to use --focus or all 42)",
    )
    parser.add_argument(
        "--focus", action="store_true",
        help="Use the curated 10 high-activity codes instead of all 42",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip codes already completed in a previous run (reads .progress.json)",
    )
    parser.add_argument(
        "--months", type=int, default=24,
        help="Lookback window in months (default: 24)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Seconds between API calls (default: 1.5)",
    )
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    api_key = env.get("SAM_GOV_API_KEY") or os.getenv("SAM_GOV_API_KEY", "")
    if not api_key:
        print(f"ERROR: SAM_GOV_API_KEY not found in {ENV_PATH}")
        sys.exit(1)

    to_dt   = datetime.utcnow()
    from_dt = to_dt - timedelta(days=args.months * 30)

    if args.codes:
        target_codes = args.codes
    elif args.focus:
        target_codes = FOCUS_CODES
    else:
        target_codes = list(NAICS_CODES.keys())

    done = load_progress() if args.resume else set()
    if args.resume and done:
        print(f"Resuming — {len(done)} code(s) already completed: {', '.join(sorted(done))}")
        # Keep existing CSV as-is; summaries will be rebuilt from all rows at the end
    elif not args.resume:
        # Fresh run — clear any previous raw CSV so we don't double-count
        if RAW_CSV.exists():
            RAW_CSV.unlink()
        clear_progress()

    pending = [c for c in target_codes if c not in done]

    chunks_per_code = len(date_chunks(from_dt, to_dt))
    print(f"\nHorizon Search — SAM.gov Award Notice Fetcher")
    print(f"Date range  : {from_dt.strftime('%m/%d/%Y')} → {to_dt.strftime('%m/%d/%Y')} ({args.months} months, {chunks_per_code} window(s)/code)")
    print(f"Target codes: {len(target_codes)}  |  Remaining: {len(pending)}  |  Done: {len(done)}")
    print(f"Delay       : {args.delay}s  |  Output: {DATA_DIR.relative_to(HERE.parent)}/\n")

    with httpx.Client() as client:
        for i, naics in enumerate(pending, 1):
            label = NAICS_CODES.get(naics, naics)
            print(f"[{i}/{len(pending)}] {naics} — {label}")
            rows = fetch_all_for_naics(client, api_key, naics, from_dt, to_dt, args.delay)
            if rows:
                append_raw_csv(rows)
            done.add(naics)
            save_progress(done)
            print(f"  ✓ saved {len(rows):,} rows to awards_raw.csv\n")
            if i < len(pending):
                time.sleep(args.delay)

    # Rebuild summary CSVs from the full raw file
    all_rows = read_all_raw()
    if not all_rows:
        print("No award notices collected.")
        sys.exit(0)

    print(f"{'─'*60}")
    print(f"Total collected: {len(all_rows):,} award notices across {len(done)} NAICS codes")
    print(f"Rebuilding summaries …\n")

    city_fields = [
        "naics_code", "naics_label", "city", "state",
        "award_count", "total_dollars", "avg_dollars", "veteran_awards", "top_agencies",
    ]
    agency_fields = [
        "agency", "naics_code", "naics_label",
        "award_count", "total_dollars", "avg_dollars", "veteran_awards", "top_cities",
    ]
    write_csv(CITY_CSV,   build_city_summary(all_rows),   city_fields)
    write_csv(AGENCY_CSV, build_agency_summary(all_rows), agency_fields)

    if len(done) == len(target_codes):
        clear_progress()
        print(f"\nRun complete — progress file cleared.")
    else:
        remaining = [c for c in target_codes if c not in done]
        print(f"\n{len(remaining)} code(s) not yet fetched. Re-run with --resume to continue.")

    print(f"\nDone. Sort awards_by_city.csv by total_dollars to find outreach hotspots.")


if __name__ == "__main__":
    main()
