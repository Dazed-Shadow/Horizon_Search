from typing import Optional
from pydantic import BaseModel


class MonthlyCount(BaseModel):
    month: str          # "2025-06"
    month_label: str    # "Jun 2025"
    count: int
    is_current: bool    # True if this is the current (partial) month


class BidTimingAdvice(BaseModel):
    best_months: list[str]    # top 3 month_labels by count, desc
    slowest_months: list[str] # bottom 3 month_labels by count, asc
    recommendation: str       # 2-3 sentence plain-language guidance
    prep_window: str          # e.g. "Begin preparing by June 2025"


class FYForecast(BaseModel):
    fy_label: str         # "FY2026"
    is_surge_window: bool # True if Jun 1 – Sep 30
    days_remaining: int   # days until Sep 30 of current FY
    message: str          # plain-language callout


class AgencyCount(BaseModel):
    agency: str
    count: int


class AgencyBreakdown(BaseModel):
    agencies: list[AgencyCount]  # sorted desc, max 5
    total_agencies_active: int
    interpretation: str


class NaicsInsightResponse(BaseModel):
    naics_code: str
    set_aside_code: Optional[str]
    set_aside_label: Optional[str]
    months: list[MonthlyCount]   # oldest-first, length == lookback_months
    total_opportunities: int
    avg_per_month: float         # mean of completed months (excludes current partial)
    peak_month: str              # month_label of highest count
    interpretation: str          # plain-language summary, generated server-side
    bid_timing: Optional[BidTimingAdvice] = None
    fy_forecast: Optional[FYForecast] = None
    agency_breakdown: Optional[AgencyBreakdown] = None
