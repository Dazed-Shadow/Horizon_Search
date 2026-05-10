import os
from fastapi import APIRouter

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/status")
async def config_status():
    api_key = os.getenv("SAM_GOV_API_KEY", "")
    configured = bool(api_key and api_key not in ("", "your_api_key_here"))
    return {
        "api_key_configured": configured,
        "message": "Ready" if configured else (
            "SAM.gov API key not set — copy backend/.env.example to backend/.env "
            "and add your key from sam.gov/profile/details"
        ),
    }
