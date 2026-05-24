"""
NAICS Activity Insights — 12-month historical contract count aggregation.

For a given NAICS code + optional set-aside filter, queries SAM.gov for the
number of contracts posted each month for the past N months, plus per-agency
breakdowns across 15 top federal buyers. Results are cached aggressively
(24h for complete months/agencies, 5m for the current partial month) to
stay well within SAM.gov's free-tier rate limit.

Rate-limit math: 12 month calls + 15 agency calls = 27 API calls per first
request. With 24h caching, every subsequent request costs zero calls.
asyncio.Semaphore(3) prevents burst throttling on the first cold load.
"""
import asyncio
import httpx
import os
import time
from calendar import monthrange
from datetime import datetime, date
from typing import Optional

from models.insights import (
    MonthlyCount, NaicsInsightResponse,
    BidTimingAdvice, FYForecast, AgencyCount, AgencyBreakdown,
)
from services.sam_gov import SAM_BASE, SET_ASIDE_LABELS

# ---------------------------------------------------------------------------
# In-memory cache — { key: (monotonic_ts, count) }
# Keys: "insight:<naics>:<set_aside>:<YYYY-MM>"  (monthly)
#       "agency:<naics>:<set_aside>:<agency_name>"  (agency totals)
# ---------------------------------------------------------------------------
_insight_cache: dict[str, tuple[float, int]] = {}
_TTL_HISTORICAL = 86400  # 24h — completed months / agency totals are stable
_TTL_CURRENT = 300       # 5m  — current month is still accumulating

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# 15 major federal agencies — covers the vast majority of set-aside contracts.
TOP_AGENCIES = [
    "Department of Defense",
    "Department of Veterans Affairs",
    "Department of Homeland Security",
    "Department of Health and Human Services",
    "General Services Administration",
    "Department of Energy",
    "Department of Justice",
    "Department of Transportation",
    "Department of Agriculture",
    "Department of the Interior",
    "Department of State",
    "Department of the Treasury",
    "National Aeronautics and Space Administration",
    "Social Security Administration",
    "Environmental Protection Agency",
]


def _cache_key(naics: str, set_aside: Optional[str], month: str) -> str:
    return f"insight:{naics}:{set_aside or 'ALL'}:{month}"


def _agency_cache_key(naics: str, set_aside: Optional[str], agency: str) -> str:
    return f"agency:{naics}:{set_aside or 'ALL'}:{agency}"


def _cache_get(key: str, ttl: float) -> Optional[int]:
    entry = _insight_cache.get(key)
    if entry and (time.monotonic() - entry[0]) < ttl:
        return entry[1]
    return None


def _cache_set(key: str, count: int) -> None:
    _insight_cache[key] = (time.monotonic(), count)


def _month_label(year: int, month: int) -> str:
    return f"{MONTH_NAMES[month - 1]} {year}"


def _build_month_sequence(lookback: int) -> list[tuple[int, int]]:
    """Return list of (year, month) tuples, oldest first, for the past N months."""
    now = datetime.utcnow()
    year, month = now.year, now.month
    months: list[tuple[int, int]] = []
    for _ in range(lookback):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


async def _fetch_month_count(
    naics: str,
    set_aside: Optional[str],
    year: int,
    month: int,
    api_key: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> int:
    now = datetime.utcnow()
    is_current = (year == now.year and month == now.month)
    ttl = _TTL_CURRENT if is_current else _TTL_HISTORICAL
    key = _cache_key(naics, set_aside, f"{year:04d}-{month:02d}")

    cached = _cache_get(key, ttl)
    if cached is not None:
        return cached

    _, last_day = monthrange(year, month)
    fmt = "%m/%d/%Y"
    params: dict = {
        "api_key": api_key,
        "naicsCode": naics,
        "limit": 1,
        "offset": 0,
        "postedFrom": date(year, month, 1).strftime(fmt),
        "postedTo": date(year, month, last_day).strftime(fmt),
    }
    if set_aside:
        params["typeOfSetAside"] = set_aside

    async with sem:
        try:
            r = await client.get(SAM_BASE, params=params)
            r.raise_for_status()
            raw = r.json().get("totalRecords", 0)
            count = int(raw) if raw else 0
        except Exception:
            count = 0

    _cache_set(key, count)
    return count


async def _fetch_agency_count(
    naics: str,
    set_aside: Optional[str],
    agency: str,
    api_key: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> tuple[str, int]:
    """Return (agency, total_contracts_in_last_12_months) for a single agency."""
    key = _agency_cache_key(naics, set_aside, agency)
    cached = _cache_get(key, _TTL_HISTORICAL)
    if cached is not None:
        return agency, cached

    today = date.today()
    twelve_months_ago = date(today.year - 1, today.month, 1)
    fmt = "%m/%d/%Y"
    params: dict = {
        "api_key": api_key,
        "naicsCode": naics,
        "limit": 1,
        "offset": 0,
        "postedFrom": twelve_months_ago.strftime(fmt),
        "postedTo": today.strftime(fmt),
        "organizationName": agency,
    }
    if set_aside:
        params["typeOfSetAside"] = set_aside

    async with sem:
        try:
            r = await client.get(SAM_BASE, params=params)
            r.raise_for_status()
            raw = r.json().get("totalRecords", 0)
            count = int(raw) if raw else 0
        except Exception:
            count = 0

    _cache_set(key, count)
    return agency, count


def _generate_bid_timing(months: list[MonthlyCount]) -> Optional[BidTimingAdvice]:
    complete = [m for m in months if not m.is_current]
    if not complete or all(m.count == 0 for m in complete):
        return None

    sorted_desc = sorted(complete, key=lambda m: m.count, reverse=True)
    sorted_asc = sorted(complete, key=lambda m: m.count)

    best = [m.month_label for m in sorted_desc[:3] if m.count > 0]
    slowest = [m.month_label for m in sorted_asc[:3] if m.count < sorted_desc[0].count]

    if not best:
        return None

    if len(best) == 1:
        rec = (
            f"Activity concentrates in {best[0]}. "
            "Plan to have your capability statement and SAM.gov registration current "
            "at least 30 days before that month."
        )
    elif len(best) == 2:
        rec = (
            f"Activity peaks in {best[0]} and {best[1]}. "
            "Build your capability statement and pricing well before these months "
            "so you can respond the day an opportunity drops."
        )
    else:
        rec = (
            f"Activity peaks in {best[0]}, {best[1]}, and {best[2]}. "
            "Maintain a ready capability statement and a current SAM.gov registration "
            "so you can respond quickly when opportunities open."
        )

    # Prep window = one calendar month before the top peak month
    top = sorted_desc[0]
    peak_year, peak_month_num = int(top.month[:4]), int(top.month[5:7])
    if peak_month_num == 1:
        prep_month_num, prep_year = 12, peak_year - 1
    else:
        prep_month_num, prep_year = peak_month_num - 1, peak_year

    prep_window = f"Begin preparing by {MONTH_NAMES[prep_month_num - 1]} {prep_year}"

    return BidTimingAdvice(
        best_months=best,
        slowest_months=slowest[:3],
        recommendation=rec,
        prep_window=prep_window,
    )


def _generate_fy_forecast() -> FYForecast:
    today = date.today()
    month, year = today.month, today.year

    # US FY ends Sep 30 — FY label is the calendar year of the end date.
    fy_end_year = year if month <= 9 else year + 1
    fy_label = f"FY{fy_end_year}"
    fy_end = date(fy_end_year, 9, 30)
    days_remaining = max((fy_end - today).days, 1)

    # Surge window: June 1 through September 30
    is_surge_window = month in (6, 7, 8, 9)

    if is_surge_window:
        if days_remaining <= 30:
            message = (
                f"You are in the final stretch of {fy_label} — only {days_remaining} days "
                "until the fiscal year closes September 30. Agencies are racing to obligate "
                "remaining budget. Monitor SAM.gov daily and be ready to respond within hours."
            )
        else:
            message = (
                f"Federal fiscal year-end surge is underway ({fy_label} closes September 30, "
                f"{days_remaining} days away). Agencies accelerate spending July–September "
                "to avoid 'use it or lose it' budget expiration — high-volume period for awards."
            )
    elif month in (10, 11, 12):
        message = (
            f"{fy_label} just started October 1. New budgets are being allocated — "
            "expect slower contracting activity in Q1 as agencies finalize acquisition plans. "
            f"Use this period to refine your capability statement. {days_remaining} days until this FY closes."
        )
    else:
        # January–May
        message = (
            f"Currently mid-{fy_label} (ends September 30, {days_remaining} days away). "
            "Steady contracting activity — a good window to build relationships with "
            "contracting officers and sharpen your capability statement before the summer surge."
        )

    return FYForecast(
        fy_label=fy_label,
        is_surge_window=is_surge_window,
        days_remaining=days_remaining,
        message=message,
    )


def _generate_agency_breakdown(
    naics: str,
    set_aside_label: Optional[str],
    agency_results: list[tuple[str, int]],
) -> Optional[AgencyBreakdown]:
    active = [(agency, count) for agency, count in agency_results if count > 0]
    if not active:
        return None

    active.sort(key=lambda x: x[1], reverse=True)
    top5 = [AgencyCount(agency=a, count=c) for a, c in active[:5]]
    total_active = len(active)

    filter_desc = f"{set_aside_label} contracts" if set_aside_label else "contracts"
    top_agency, top_count = active[0]

    if total_active == 1:
        interp = (
            f"{top_agency} is the only active buyer for {filter_desc} under NAICS {naics} "
            "in the past 12 months. Focus your outreach there."
        )
    else:
        interp = (
            f"{top_agency} leads with {top_count} {filter_desc} under NAICS {naics} "
            f"over the past 12 months, across {total_active} active agencies. "
            "Prioritize your business development outreach to the top buyers."
        )

    return AgencyBreakdown(
        agencies=top5,
        total_agencies_active=total_active,
        interpretation=interp,
    )


def _generate_interpretation(
    naics: str,
    set_aside_label: Optional[str],
    months: list[MonthlyCount],
    total: int,
    avg: float,
    peak_obj: Optional[MonthlyCount],
) -> str:
    filter_desc = f"{set_aside_label} contracts" if set_aside_label else "contracts"

    if total == 0:
        return (
            f"No {filter_desc} were posted under NAICS {naics} in the past 12 months. "
            "This code may have limited activity for this set-aside type. "
            "Try removing the set-aside filter, or check a related NAICS code."
        )

    fy_note = ""
    if peak_obj:
        peak_month_num = int(peak_obj.month.split("-")[1])
        if peak_month_num in (7, 8, 9):
            fy_note = (
                " This aligns with federal fiscal year-end spending — agencies accelerate "
                "procurement in July–September before the FY closes on September 30."
            )

    volume_note = ""
    if avg >= 4:
        volume_note = " This is healthy pipeline activity for this NAICS/set-aside combination."
    elif avg >= 1.5:
        volume_note = " Moderate activity — worth preparing your capability statement now."
    else:
        volume_note = (
            " Low volume for this combination. Consider also searching "
            "related NAICS codes or a broader set-aside filter."
        )

    peak_text = ""
    if peak_obj and peak_obj.count > 0:
        plural = "s" if peak_obj.count != 1 else ""
        peak_text = f" Activity peaked in {peak_obj.month_label} with {peak_obj.count} posting{plural}.{fy_note}"

    return (
        f"Over the past 12 months, {total} {filter_desc} "
        f"were posted under NAICS {naics}.{peak_text} "
        f"On average, about {avg:.1f} contract{'s' if avg != 1 else ''} per month "
        f"match this profile.{volume_note}"
    )


async def get_naics_activity(
    naics_code: str,
    set_aside: Optional[str] = None,
    lookback_months: int = 12,
) -> NaicsInsightResponse:
    api_key = os.getenv("SAM_GOV_API_KEY", "")
    set_aside_label = SET_ASIDE_LABELS.get(set_aside) if set_aside else None
    month_pairs = _build_month_sequence(lookback_months)
    now = datetime.utcnow()

    sem = asyncio.Semaphore(3)
    async with httpx.AsyncClient(timeout=20) as client:
        month_tasks = [
            _fetch_month_count(naics_code, set_aside, y, m, api_key, client, sem)
            for y, m in month_pairs
        ]
        agency_tasks = [
            _fetch_agency_count(naics_code, set_aside, agency, api_key, client, sem)
            for agency in TOP_AGENCIES
        ]
        all_results = await asyncio.gather(*month_tasks, *agency_tasks)

    counts = all_results[:len(month_pairs)]
    agency_results = list(all_results[len(month_pairs):])

    months: list[MonthlyCount] = [
        MonthlyCount(
            month=f"{y:04d}-{m:02d}",
            month_label=_month_label(y, m),
            count=count,
            is_current=(y == now.year and m == now.month),
        )
        for (y, m), count in zip(month_pairs, counts)
    ]

    complete = [mo for mo in months if not mo.is_current]
    avg = sum(mo.count for mo in complete) / len(complete) if complete else 0.0
    total = sum(mo.count for mo in months)
    peak_obj = max(months, key=lambda mo: mo.count) if months else None

    return NaicsInsightResponse(
        naics_code=naics_code,
        set_aside_code=set_aside,
        set_aside_label=set_aside_label,
        months=months,
        total_opportunities=total,
        avg_per_month=round(avg, 1),
        peak_month=peak_obj.month_label if peak_obj else "N/A",
        interpretation=_generate_interpretation(
            naics_code, set_aside_label, months, total, avg, peak_obj
        ),
        bid_timing=_generate_bid_timing(months),
        fy_forecast=_generate_fy_forecast(),
        agency_breakdown=_generate_agency_breakdown(
            naics_code, set_aside_label, agency_results
        ),
    )
