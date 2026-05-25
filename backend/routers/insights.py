import logging
import httpx
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from services.insights import get_naics_activity
from models.insights import NaicsInsightResponse

log = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/naics-activity", response_model=NaicsInsightResponse)
async def naics_activity(
    naics_code: str = Query(..., description="6-digit NAICS code"),
    set_aside: Optional[str] = Query(default=None, description="Set-aside type code (e.g. SDVOSBC)"),
    months: int = Query(default=24, ge=3, le=24, description="Months to look back (3–24)"),
):
    """
    Return monthly contract-posting counts for a NAICS code over the past N months.
    Results are cached 24h for historical months and 5m for the current partial month.
    Each unique NAICS+set_aside combination costs 12 SAM.gov API calls on first load.
    """
    try:
        return await get_naics_activity(naics_code, set_aside, months)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="SAM.gov daily search limit reached. Please wait a few minutes.",
            )
        raise HTTPException(status_code=502, detail=f"SAM.gov returned {exc.response.status_code}")
    except Exception as exc:
        log.exception("NAICS activity fetch failed for %s", naics_code)
        raise HTTPException(status_code=502, detail=str(exc))
