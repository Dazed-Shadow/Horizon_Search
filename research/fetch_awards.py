#!/usr/bin/env python3
"""
SAM.gov Award Notice downloader — local research tool.

Pulls Award Notices (ptype=a) for the past 24 months by NAICS code,
then writes three CSVs for outreach planning:

  data/awards_raw.csv       — one row per award notice
  data/awards_by_city.csv   — NAICS × city × state: count + total $
  data/awards_by_agency.csv — agency × NAICS: count + total $ + city breakdown

Usage (run from repo root OR research/ dir):
  python research/fetch_awards.py                    # all 42 NAICS codes
  python research/fetch_awards.py 541512             # single code
  python research/fetch_awards.py 541512 541519      # multiple codes
  python research/fetch_awards.py --delay 2.0        # slower (if hitting 429s)
  python research/fetch_awards.py --months 12        # shorter lookback

Requirements: httpx (already installed via backend)
API key: read from backend/.env automatically
"""

import argparse
import csv
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
HERE      = Path(__file__).resolve().parent
DATA_DIR  = HERE / "data"
ENV_PATH  = HERE.parent / "backend" / ".env"
SAM_BASE  = "https://api.sam.gov/opportunities/v2/search"

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


# ---------------------------------------------------------------------------
# Env loading — no external dependency needed
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
# SAM.gov fetch — single page of award notices for one NAICS code
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
        "ptype":      "a",          # Award Notices only
        "naicsCode":  naics,
        "postedFrom": posted_from,
        "postedTo":   posted_to,
        "limit":      page_size,
        "offset":     offset,
    }
    resp = client.get(SAM_BASE, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Parse a single opportunity dict into a flat row dict
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
        awardee    = (award.get("awardee") or {})
        awardee_nm = (
            awardee.get("name")
            or awardee.get("legalBusinessName")
            or ""
        )
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
            "agency":          opp.get("fullParentPathName")
                               or opp.get("department")
                               or opp.get("organizationName")
                               or "",
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
# Fetch all pages for one NAICS code
# ---------------------------------------------------------------------------
def fetch_all_for_naics(
    client: httpx.Client,
    api_key: str,
    naics: str,
    posted_from: str,
    posted_to: str,
    delay: float = 1.0,
) -> list[dict]:
    rows = []
    offset = 0
    total_known = None

    while True:
        try:
            data = fetch_page(client, api_key, naics, posted_from, posted_to, offset)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"  [429] Rate limited — waiting 60s …")
                time.sleep(60)
                continue
            print(f"  [HTTP {e.response.status_code}] {e}")
            break
        except Exception as e:
            print(f"  [ERROR] {e}")
            break

        opps = data.get("opportunitiesData") or []
        if total_known is None:
            raw_total = data.get("totalRecords", 0)
            try:
                total_known = int(raw_total)
            except (ValueError, TypeError):
                total_known = 0
            print(f"  {total_known:,} award notices found", end="", flush=True)

        for opp in opps:
            row = parse_opportunity(opp, naics)
            if row:
                rows.append(row)

        offset += len(opps)
        print(f"\r  {len(rows):,} / {total_known:,} fetched   ", end="", flush=True)

        # Stop when we've retrieved everything or hit SAM.gov's 10,000 record cap
        if not opps or offset >= total_known or offset >= 10_000:
            break

        time.sleep(delay)

    print()  # newline after progress
    return rows


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------
def build_city_summary(rows: list[dict]) -> list[dict]:
    """Roll up rows → NAICS × city × state with count + total $."""
    bucket: dict[tuple, dict] = defaultdict(lambda: {
        "count": 0, "total_amount": 0.0, "veteran_count": 0,
        "agencies": set(),
    })

    for r in rows:
        key = (r["naics_code"], r["naics_label"], r["city"], r["state"])
        b = bucket[key]
        b["count"] += 1
        b["total_amount"] += r["award_amount"] or 0
        if r["is_veteran"]:
            b["veteran_count"] += 1
        if r["agency"]:
            b["agencies"].add(r["agency"].split("|")[0].strip())

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

    # Sort by total $ desc
    return sorted(summary, key=lambda x: x["total_dollars"], reverse=True)


def build_agency_summary(rows: list[dict]) -> list[dict]:
    """Roll up rows → agency × NAICS with count + total $ + top cities."""
    bucket: dict[tuple, dict] = defaultdict(lambda: {
        "count": 0, "total_amount": 0.0, "veteran_count": 0,
        "cities": defaultdict(int),
    })

    for r in rows:
        agency = r["agency"].split("|")[0].strip() if r["agency"] else "Unknown"
        key = (agency, r["naics_code"], r["naics_label"])
        b = bucket[key]
        b["count"] += 1
        b["total_amount"] += r["award_amount"] or 0
        if r["is_veteran"]:
            b["veteran_count"] += 1
        loc = f"{r['city']}, {r['state']}" if r["city"] else r["state"]
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
# CSV writer
# ---------------------------------------------------------------------------
def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows → {path.relative_to(HERE.parent)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SAM.gov award notices by NAICS code")
    parser.add_argument(
        "codes", nargs="*",
        help="NAICS codes to fetch (default: all 42 common codes)",
    )
    parser.add_argument(
        "--months", type=int, default=24,
        help="Lookback window in months (default: 24)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.2,
        help="Seconds between API calls (default: 1.2, free tier limit ~0.8 req/s)",
    )
    args = parser.parse_args()

    # Load API key
    env = load_env(ENV_PATH)
    api_key = env.get("SAM_GOV_API_KEY") or os.getenv("SAM_GOV_API_KEY", "")
    if not api_key:
        print(f"ERROR: SAM_GOV_API_KEY not found in {ENV_PATH}")
        sys.exit(1)

    # Date range
    fmt = "%m/%d/%Y"
    to_date   = datetime.utcnow()
    from_date = to_date - timedelta(days=args.months * 30)
    posted_from = from_date.strftime(fmt)
    posted_to   = to_date.strftime(fmt)

    # Target codes
    target_codes = args.codes if args.codes else list(NAICS_CODES.keys())
    invalid = [c for c in target_codes if c not in NAICS_CODES]
    if invalid:
        print(f"Unknown NAICS codes (will still fetch): {invalid}")

    print(f"\nHorizon Search — SAM.gov Award Notice Fetcher")
    print(f"Date range : {posted_from}  →  {posted_to}  ({args.months} months)")
    print(f"NAICS codes: {len(target_codes)}")
    print(f"Delay      : {args.delay}s between requests")
    print(f"Output     : {DATA_DIR.relative_to(HERE.parent)}/\n")

    all_rows: list[dict] = []

    with httpx.Client() as client:
        for i, naics in enumerate(target_codes, 1):
            label = NAICS_CODES.get(naics, naics)
            print(f"[{i}/{len(target_codes)}] {naics} — {label}")
            rows = fetch_all_for_naics(
                client, api_key, naics,
                posted_from, posted_to,
                delay=args.delay,
            )
            all_rows.extend(rows)
            if i < len(target_codes):
                time.sleep(args.delay)

    if not all_rows:
        print("\nNo award notices found. Check your API key and date range.")
        sys.exit(0)

    print(f"\n{'─'*60}")
    print(f"Total award notices collected: {len(all_rows):,}")
    print(f"Writing CSVs …\n")

    # Raw awards
    raw_fields = [
        "notice_id", "posted_date", "naics_code", "naics_label",
        "city", "state", "agency", "sub_agency", "office",
        "awardee", "award_amount", "set_aside_code", "set_aside_label",
        "is_veteran", "title", "ui_link",
    ]
    write_csv(DATA_DIR / "awards_raw.csv", all_rows, raw_fields)

    # City summary
    city_summary = build_city_summary(all_rows)
    city_fields = [
        "naics_code", "naics_label", "city", "state",
        "award_count", "total_dollars", "avg_dollars",
        "veteran_awards", "top_agencies",
    ]
    write_csv(DATA_DIR / "awards_by_city.csv", city_summary, city_fields)

    # Agency summary
    agency_summary = build_agency_summary(all_rows)
    agency_fields = [
        "agency", "naics_code", "naics_label",
        "award_count", "total_dollars", "avg_dollars",
        "veteran_awards", "top_cities",
    ]
    write_csv(DATA_DIR / "awards_by_agency.csv", agency_summary, agency_fields)

    print(f"\nDone. Open data/ in Excel or import into Notion for analysis.")
    print(f"Outreach tip: sort awards_by_city.csv by total_dollars for each NAICS")
    print(f"to find cities where federal spend is highest in your target industries.")


if __name__ == "__main__":
    main()
