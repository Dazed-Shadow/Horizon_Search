"""
NAICS Activity Insights — 12-month historical contract count aggregation.

For a given NAICS code + optional set-aside filter, queries SAM.gov for the
number of contracts posted each month for the past N months. Results are cached
aggressively (24h for complete months, 5m for the current partial month) to
stay well within SAM.gov's free-tier rate limit.

Rate-limit math: 12 API calls per insight request. With 24h caching, the second
request for the same NAICS+set-aside combo costs zero calls. Worst case for a
busy day: ~80 unique combos × 12 = 960 calls, still under the 1,000/day limit.
asyncio.Semaphore(3) prevents burst throttling on the first load.
"""
import asyncio
import httpx
import os
import time
from calendar import monthrange
from datetime import datetime, date
from typing import Optional

from models.insights import MonthlyCount, NaicsInsightResponse
from services.sam_gov import SAM_BASE, SET_ASIDE_LABELS

# ---------------------------------------------------------------------------
# In-memory cache — { "insight:<naics>:<set_aside>:<YYYY-MM>": (ts, count) }
# ---------------------------------------------------------------------------
_insight_cache: dict[str, tuple[float, int]] = {}
_TTL_HISTORICAL = 86400  # 24h — completed months are fully deterministic
_TTL_CURRENT = 300       # 5m  — current month is still accumulating

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _cache_key(naics: str, set_aside: Optional[str], month: str) -> str:
    return f"insight:{naics}:{set_aside or 'ALL'}:{month}"


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
        counts = await asyncio.gather(*[
            _fetch_month_count(naics_code, set_aside, y, m, api_key, client, sem)
            for y, m in month_pairs
        ])

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
    )
