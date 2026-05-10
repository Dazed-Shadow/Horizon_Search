from pydantic import BaseModel
from typing import Optional


class ContractSearchParams(BaseModel):
    keyword: str = ""
    set_aside: Optional[str] = None        # e.g. "SDVOSBC", "8AN", "SBA"
    naics_code: Optional[str] = None
    agency: Optional[str] = None
    solicitation_type: Optional[str] = None  # o=solicitation, p=presolicitation, r=sources sought
    posted_from: Optional[str] = None       # MM/DD/YYYY
    posted_to: Optional[str] = None
    response_deadline_from: Optional[str] = None
    response_deadline_to: Optional[str] = None
    state: Optional[str] = None            # place of performance state
    limit: int = 25
    offset: int = 0


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class Contract(BaseModel):
    notice_id: str
    title: str
    solicitation_number: Optional[str] = None
    agency: Optional[str] = None
    sub_agency: Optional[str] = None
    office: Optional[str] = None
    posted_date: Optional[str] = None
    response_deadline: Optional[str] = None
    solicitation_type: Optional[str] = None
    solicitation_type_label: Optional[str] = None
    set_aside_code: Optional[str] = None
    set_aside_label: Optional[str] = None
    naics_code: Optional[str] = None
    naics_description: Optional[str] = None
    place_of_performance: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    award_amount: Optional[float] = None
    ui_link: Optional[str] = None
    contact: Optional[ContactInfo] = None


class ContractSearchResult(BaseModel):
    total: int
    limit: int
    offset: int
    contracts: list[Contract]
