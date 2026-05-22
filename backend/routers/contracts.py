import logging
import httpx
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

log = logging.getLogger(__name__)

from services.sam_gov import search_contracts, get_contract_by_notice_id, SET_ASIDE_LABELS, SOLICITATION_TYPE_LABELS
from models.contract import Contract, ContractSearchResult

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
    open_only: bool = Query(default=True, description="Exclude award notices and justifications"),
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
            open_only=open_only,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="SAM.gov daily search limit reached. Please wait a few minutes and try again.",
            )
        log.error("SAM.gov HTTP error %s", exc.response.status_code)
        raise HTTPException(status_code=502, detail=f"SAM.gov returned {exc.response.status_code}")
    except Exception as exc:
        log.exception("Search failed")
        raise HTTPException(status_code=502, detail=f"SAM.gov API error: {str(exc)}")


@router.get("/filters/set-asides")
async def list_set_asides():
    """Return all supported set-aside codes and their labels."""
    return [{"code": k, "label": v} for k, v in SET_ASIDE_LABELS.items()]


@router.get("/filters/solicitation-types")
async def list_solicitation_types():
    """Return all solicitation type codes and labels."""
    return [{"code": k, "label": v} for k, v in SOLICITATION_TYPE_LABELS.items()]


# Deep-link support: must be last — /{notice_id} is a wildcard and would shadow /filters/* if placed first.
@router.get("/{notice_id}", response_model=Contract)
async def get_contract(notice_id: str):
    try:
        contract = await get_contract_by_notice_id(notice_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"SAM.gov returned {exc.response.status_code}")
    except Exception as exc:
        log.exception("Notice ID lookup failed")
        raise HTTPException(status_code=502, detail=str(exc))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
