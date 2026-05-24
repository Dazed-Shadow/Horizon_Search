from typing import Optional
from pydantic import BaseModel


class MonthlyCount(BaseModel):
    month: str          # "2025-06"
    month_label: str    # "Jun 2025"
    count: int
    is_current: bool    # True if this is the current (partial) month


class NaicsInsightResponse(BaseModel):
    naics_code: str
    set_aside_code: Optional[str]
    set_aside_label: Optional[str]
    months: list[MonthlyCount]   # oldest-first, length == lookback_months
    total_opportunities: int
    avg_per_month: float         # mean of completed months (excludes current partial)
    peak_month: str              # month_label of highest count
    interpretation: str          # plain-language summary, generated server-side
