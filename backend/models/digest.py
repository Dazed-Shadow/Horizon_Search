from pydantic import BaseModel
from typing import Optional


class KeyDate(BaseModel):
    label: str
    date: Optional[str] = None
    context: Optional[str] = None  # surrounding sentence for disambiguation


class ContractDigest(BaseModel):
    notice_id: str
    scope_summary: Optional[str] = None         # 1–2 sentence plain-language summary
    deliverables: list[str] = []                # identified deliverables
    submission_requirements: list[str] = []     # what the bid must contain
    evaluation_criteria: list[str] = []         # how the bid will be judged
    period_of_performance: Optional[str] = None # e.g. "12 months", "FY26 base + 4 option years"
    estimated_value: Optional[str] = None       # raw text: "$5M NTE", "TBD", or None
    key_dates: list[KeyDate] = []
    extraction_confidence: str = "low"          # "high" | "medium" | "low"
