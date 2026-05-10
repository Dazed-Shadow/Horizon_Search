from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from services.sam_gov import search_contracts, SET_ASIDE_LABELS, SOLICITATION_TYPE_LABELS
from models.contract import ContractSearchResult

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/search", response_model=ContractSearchResult)
async def search(
    keyword: str = Query(default="", description="Full-text keyword search"),
    set_aside: Optional[str] = Query(default=None, description="Set-aside type code (e.g. SDVOSBC, 8AN, SBA)"),
    naics_code: Optional[str] = Query(default=None, description="6-digit NAICS code"),
    agency: Optional[str] = Query(default=None, description="Agency / department name"),
    solicitation_type: Optional[str] = Query(default=None, description="Solicitation type code (o, p, r, k, ...)"),
    posted_from: Optional[str] = Query(default=None, description="Posted date from MM/DD/YYYY"),
    posted_to: Optional[str] = Query(default=None, description="Posted date to MM/DD/YYYY"),
    response_deadline_from: Optional[str] = Query(default=None, description="Response deadline from MM/DD/YYYY"),
    response_deadline_to: Optional[str] = Query(default=None, description="Response deadline to MM/DD/YYYY"),
    state: Optional[str] = Query(default=None, description="Place of performance state code (e.g. TX, CA)"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return await search_contracts(
            keyword=keyword,
            set_aside=set_aside,
            naics_code=naics_code,
            agency=agency,
            solicitation_type=solicitation_type,
            posted_from=posted_from,
            posted_to=posted_to,
            response_deadline_from=response_deadline_from,
            response_deadline_to=response_deadline_to,
            state=state,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SAM.gov API error: {str(exc)}")


@router.get("/filters/set-asides")
async def list_set_asides():
    """Return all supported set-aside codes and their labels."""
    return [{"code": k, "label": v} for k, v in SET_ASIDE_LABELS.items()]


@router.get("/filters/solicitation-types")
async def list_solicitation_types():
    """Return all solicitation type codes and labels."""
    return [{"code": k, "label": v} for k, v in SOLICITATION_TYPE_LABELS.items()]
