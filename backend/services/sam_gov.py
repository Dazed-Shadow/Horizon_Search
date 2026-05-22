import hashlib
import httpx
import os
import time
from datetime import datetime, timedelta
from typing import Optional

from models.contract import Contract, ContractSearchResult, ContactInfo

SAM_BASE = "https://api.sam.gov/opportunities/v2/search"

# ---------------------------------------------------------------------------
# Simple in-memory response cache — avoids burning SAM.gov API quota on
# repeat searches. Cache entries expire after CACHE_TTL seconds.
# ---------------------------------------------------------------------------
_CACHE_TTL = 300  # 5 minutes
_response_cache: dict = {}


def _cache_key(params: dict) -> str:
    """SHA-256 fingerprint of query params, excluding the API key."""
    relevant = sorted((k, str(v)) for k, v in params.items() if k != "api_key")
    return hashlib.sha256(str(relevant).encode()).hexdigest()[:20]


def _cache_get(key: str) -> Optional[ContractSearchResult]:
    entry = _response_cache.get(key)
    if entry and (time.monotonic() - entry["ts"]) < _CACHE_TTL:
        return entry["result"]
    return None


def _cache_set(key: str, result: ContractSearchResult) -> None:
    _response_cache[key] = {"result": result, "ts": time.monotonic()}

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


def _str_or_none(v) -> Optional[str]:
    """Coerce v to str, returning None for None/empty."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _parse_opportunity(opp: dict) -> Optional[Contract]:
    try:
        pop = opp.get("placeOfPerformance") or {}
        if isinstance(pop, dict):
            city = (pop.get("city") or {}).get("name", "")
            state = (pop.get("state") or {}).get("code", "")
            place = ", ".join(filter(None, [city, state])) or None
        else:
            # SAM.gov sometimes returns a plain string
            place = _str_or_none(pop)

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
            notice_id=str(opp.get("noticeId") or ""),
            title=str(opp.get("title") or "Untitled"),
            solicitation_number=_str_or_none(opp.get("solicitationNumber")),
            agency=_str_or_none(opp.get("department") or opp.get("organizationName")),
            sub_agency=_str_or_none(opp.get("subtier")),
            office=_str_or_none(opp.get("office")),
            posted_date=_str_or_none(opp.get("postedDate")),
            response_deadline=_str_or_none(opp.get("responseDeadLine")),
            solicitation_type=ptype,
            solicitation_type_label=SOLICITATION_TYPE_LABELS.get(ptype, ptype),
            set_aside_code=set_aside_code,
            set_aside_label=SET_ASIDE_LABELS.get(set_aside_code, set_aside_code),
            naics_code=_str_or_none(opp.get("naicsCode")),      # API returns int
            naics_description=_str_or_none(opp.get("classificationCode")),
            place_of_performance=place,
            description=_str_or_none(opp.get("description")),
            active=opp.get("active") == "Yes" if opp.get("active") else None,
            award_amount=award_amount,
            ui_link=_str_or_none(opp.get("uiLink")),
            contact=contact,
        )
    except Exception:
        return None


AWARDED_PTYPES = {"a", "u"}  # Award Notice, Justification — not biddable

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
    open_only: bool = True,
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

    # Return cached result if still fresh
    key = _cache_key(params)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(SAM_BASE, params=params)
        response.raise_for_status()
        data = response.json()

    opportunities = data.get("opportunitiesData", []) or []
    total = data.get("totalRecords", len(opportunities))

    contracts = [c for o in opportunities if (c := _parse_opportunity(o)) is not None]

    if open_only and not solicitation_type:
        contracts = [c for c in contracts if c.solicitation_type not in AWARDED_PTYPES]

    result = ContractSearchResult(
        total=total,
        limit=limit,
        offset=offset,
        contracts=contracts,
    )
    _cache_set(key, result)
    return result


async def get_contract_by_notice_id(notice_id: str) -> Optional[Contract]:
    """Fetch a single contract by its SAM.gov notice ID for deep-link support."""
    api_key = os.getenv("SAM_GOV_API_KEY", "")
    fmt = "%m/%d/%Y"
    # SAM.gov still requires a date range even when searching by noticeId
    params = {
        "api_key": api_key,
        "noticeid": notice_id,
        "limit": 1,
        "offset": 0,
        "postedFrom": (datetime.utcnow() - timedelta(days=365)).strftime(fmt),
        "postedTo": datetime.utcnow().strftime(fmt),
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(SAM_BASE, params=params)
        response.raise_for_status()
        data = response.json()
    opportunities = data.get("opportunitiesData", []) or []
    if not opportunities:
        return None
    return _parse_opportunity(opportunities[0])
