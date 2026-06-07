"""
Tests for the RFP digest parser and endpoint.
Unit tests: pure parse_digest function — no fixtures, no I/O.
Endpoint tests: mirror test_contracts.py pattern with respx + SAMPLE_OPPORTUNITY.
"""
import pytest
import respx
import httpx
from tests.conftest import SAMPLE_OPPORTUNITY

from models.contract import Contract
from services.digest import parse_digest


SAM_URL = "https://api.sam.gov/opportunities/v2/search"

# ---------------------------------------------------------------------------
# Unit tests — parse_digest (pure function)
# ---------------------------------------------------------------------------

def test_parse_digest_extracts_scope_summary():
    contract = Contract(notice_id="x", description=(
        "SCOPE OF WORK\n"
        "The contractor shall provide IT support services for the Army. "
        "Services include help desk operations and network maintenance."
    ))
    digest = parse_digest(contract)
    assert "IT support" in (digest.scope_summary or "")


def test_parse_digest_extracts_bulleted_deliverables():
    contract = Contract(notice_id="x", description=(
        "Deliverables:\n"
        "- Monthly status reports\n"
        "- Quarterly system audits\n"
        "- Annual security review"
    ))
    digest = parse_digest(contract)
    assert len(digest.deliverables) == 3
    assert "Monthly status reports" in digest.deliverables


def test_parse_digest_extracts_evaluation_criteria():
    contract = Contract(notice_id="x", description=(
        "EVALUATION CRITERIA:\n"
        "1. Technical approach\n"
        "2. Past performance\n"
        "3. Price"
    ))
    digest = parse_digest(contract)
    assert len(digest.evaluation_criteria) == 3


def test_parse_digest_high_confidence():
    contract = Contract(notice_id="x", description=(
        "SCOPE OF WORK\nProvide services.\n\n"
        "DELIVERABLES:\n- Reports\n\n"
        "EVALUATION CRITERIA:\n- Technical\n\n"
        "PERIOD OF PERFORMANCE:\n12 months\n\n"
        "SUBMISSION INSTRUCTIONS:\nEmail proposal by deadline."
    ))
    digest = parse_digest(contract)
    assert digest.extraction_confidence == "high"


def test_parse_digest_no_structure_returns_low_confidence():
    contract = Contract(notice_id="x", description="Just a single sentence with no headers.")
    digest = parse_digest(contract)
    assert digest.extraction_confidence == "low"


def test_parse_digest_empty_description():
    contract = Contract(notice_id="x", description=None)
    digest = parse_digest(contract)
    assert digest.extraction_confidence == "low"
    assert digest.deliverables == []


# ---------------------------------------------------------------------------
# Endpoint tests — GET /api/contracts/{notice_id}/digest
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_digest_endpoint_returns_structured_fields(client):
    payload = {**SAMPLE_OPPORTUNITY, "description": (
        "SCOPE OF WORK\nProvide IT services.\n\n"
        "DELIVERABLES:\n- Monthly reports\n- Quarterly audits"
    )}
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"totalRecords": 1, "opportunitiesData": [payload]})
        )
        r = await client.get(f"/api/contracts/{payload['noticeId']}/digest")
    assert r.status_code == 200
    data = r.json()
    assert data["scope_summary"] is not None
    assert len(data["deliverables"]) == 2


@pytest.mark.asyncio
async def test_digest_endpoint_404_when_notice_missing(client):
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"totalRecords": 0, "opportunitiesData": []})
        )
        r = await client.get("/api/contracts/missing-id/digest")
    assert r.status_code == 404
