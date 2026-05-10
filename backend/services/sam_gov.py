import httpx
import os
from datetime import datetime, timedelta
from typing import Optional

from models.contract import Contract, ContractSearchResult, ContactInfo

SAM_BASE = "https://api.sam.gov/opportunities/v2/search"

# SAM.gov set-aside codes -> human-readable labels
SET_ASIDE_LABELS = {
    "SBA": "Small Business",
    "SBP": "Small Business (Partial)",
    "8A": "8(a) Sole Source",
    "8AN": "8(a) Competitive",
    "HZC": "HUBZone Set-Aside",
    "HZS": "HUBZone Sole Source",
    "SDVOSBC": "SDVOSB Competitive",
    "SDVOSBS": "SDVOSB Sole Source",
    "WOSB": "WOSB Set-Aside",
    "WOSBSS": "WOSB Sole Source",
    "EDWOSB": "EDWOSB Set-Aside",
    "EDWOSBSS": "EDWOSB Sole Source",
    "VSB": "Veteran-Owned Small Business",
    "VOSB": "Veteran-Owned Small Business",
    "IEE": "Indian Economic Enterprise",
    "ISBEE": "Indian Small Business Economic Enterprise",
    "A": "Total Small Business",
}

SOLICITATION_TYPE_LABELS = {
    "o": "Solicitation",
    "p": "Pre-Solicitation",
    "k": "Combined Synopsis/Solicitation",
    "r": "Sources Sought",
    "g": "Sale of Surplus Property",
    "s": "Special Notice",
    "i": "Intent to Bundle (DoD)",
    "a": "Award Notice",
    "u": "Justification",
}


def _parse_contact(raw: dict) -> Optional[ContactInfo]:
    if not raw:
        return None
    contacts = raw if isinstance(raw, list) else [raw]
    for c in contacts:
        if c:
            return ContactInfo(
                name=c.get("fullName") or c.get("title"),
                email=c.get("email"),
                phone=c.get("phone"),
            )
    return None


def _parse_opportunity(opp: dict) -> Contract:
    pop = opp.get("placeOfPerformance") or {}
    city = (pop.get("city") or {}).get("name", "")
    state = (pop.get("state") or {}).get("code", "")
    place = ", ".join(filter(None, [city, state])) or None

    set_aside_code = opp.get("typeOfSetAside") or None
    ptype = opp.get("type") or None

    award = opp.get("award") or {}
    try:
        award_amount = float(award.get("amount", 0) or 0) or None
    except (ValueError, TypeError):
        award_amount = None

    raw_contact = opp.get("pointOfContact")
    if isinstance(raw_contact, list):
        contact = _parse_contact(raw_contact[0] if raw_contact else None)
    else:
        contact = _parse_contact(raw_contact)

    return Contract(
        notice_id=opp.get("noticeId", ""),
        title=opp.get("title", "Untitled"),
        solicitation_number=opp.get("solicitationNumber"),
        agency=opp.get("department") or opp.get("organizationName"),
        sub_agency=opp.get("subtier"),
        office=opp.get("office"),
        posted_date=opp.get("postedDate"),
        response_deadline=opp.get("responseDeadLine"),
        solicitation_type=ptype,
        solicitation_type_label=SOLICITATION_TYPE_LABELS.get(ptype, ptype),
        set_aside_code=set_aside_code,
        set_aside_label=SET_ASIDE_LABELS.get(set_aside_code, set_aside_code),
        naics_code=opp.get("naicsCode"),
        naics_description=opp.get("classificationCode"),
        place_of_performance=place,
        description=opp.get("description"),
        active=opp.get("active") == "Yes" if opp.get("active") else None,
        award_amount=award_amount,
        ui_link=opp.get("uiLink"),
        contact=contact,
    )


async def search_contracts(
    keyword: str = "",
    set_aside: Optional[str] = None,
    naics_code: Optional[str] = None,
    agency: Optional[str] = None,
    solicitation_type: Optional[str] = None,
    posted_from: Optional[str] = None,
    posted_to: Optional[str] = None,
    response_deadline_from: Optional[str] = None,
    response_deadline_to: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> ContractSearchResult:
    api_key = os.getenv("SAM_GOV_API_KEY", "")

    params: dict = {
        "limit": limit,
        "offset": offset,
        "api_key": api_key,
    }

    if keyword:
        params["q"] = keyword
    if set_aside:
        params["typeOfSetAside"] = set_aside
    if naics_code:
        params["naicsCode"] = naics_code
    if agency:
        params["organizationName"] = agency
    if solicitation_type:
        params["ptype"] = solicitation_type
    if response_deadline_from:
        params["rdlfrom"] = response_deadline_from
    if response_deadline_to:
        params["rdlto"] = response_deadline_to
    if state:
        params["placeOfPerformanceState"] = state

    # SAM.gov v2 requires a date range — default to last 90 days if none provided
    fmt = "%m/%d/%Y"
    if posted_from:
        params["postedFrom"] = posted_from
    else:
        params["postedFrom"] = (datetime.utcnow() - timedelta(days=90)).strftime(fmt)

    if posted_to:
        params["postedTo"] = posted_to
    else:
        params["postedTo"] = datetime.utcnow().strftime(fmt)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(SAM_BASE, params=params)
        response.raise_for_status()
        data = response.json()

    opportunities = data.get("opportunitiesData", []) or []
    total = data.get("totalRecords", len(opportunities))

    contracts = [_parse_opportunity(o) for o in opportunities]

    return ContractSearchResult(
        total=total,
        limit=limit,
        offset=offset,
        contracts=contracts,
    )
