import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("SAM_GOV_API_KEY", "TEST_KEY")

# Point the insights DB at a temp file so tests never touch the real insights.db
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["INSIGHTS_DB_PATH"] = _tmp_db.name

from main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
def clear_sam_cache():
    """Wipe all caches (memory + SQLite) before every test so tests don't bleed."""
    from services.sam_gov import _response_cache
    _response_cache.clear()
    from services.insights import _insight_cache
    _insight_cache.clear()
    from services.insights_db import _db
    _db().execute("DELETE FROM monthly_counts")
    _db().execute("DELETE FROM agency_counts")
    _db().commit()
    yield
    _response_cache.clear()
    _insight_cache.clear()


# Minimal SAM.gov opportunity payload
SAMPLE_OPPORTUNITY = {
    "noticeId": "abc123",
    "title": "IT Support Services",
    "solicitationNumber": "W911NF-25-R-0001",
    "type": "o",
    "typeOfSetAside": "SDVOSBC",
    "naicsCode": "541512",
    "department": "Department of Defense",
    "subtier": "Army",
    "office": "ACC",
    "postedDate": "2025-02-01",
    "responseDeadLine": "2025-03-01",
    "active": "Yes",
    "uiLink": "https://sam.gov/opp/abc123",
    "placeOfPerformance": {
        "city": {"name": "Fort Bragg"},
        "state": {"code": "NC"},
    },
    "pointOfContact": [{"fullName": "Jane Smith", "email": "jane@army.mil", "phone": "555-1234"}],
    "award": {},
    "description": "Seeking qualified vendors for IT support.",
}

AWARD_OPPORTUNITY = {**SAMPLE_OPPORTUNITY, "noticeId": "def456", "type": "a", "title": "Awarded Contract"}

SAMPLE_SAM_RESPONSE = {
    "totalRecords": 2,
    "opportunitiesData": [SAMPLE_OPPORTUNITY, AWARD_OPPORTUNITY],
}
