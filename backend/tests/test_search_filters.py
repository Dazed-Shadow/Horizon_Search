"""
Filter-coverage tests for /api/contracts/search.

Each test verifies that when a filter param is passed to the endpoint,
the outgoing httpx request to SAM.gov carries the VERIFIED-CORRECT param name
(confirmed against SAM.gov v2 on 2026-06-03).

Pattern: respx captures the request; we assert on request.url.params.
Tests do NOT assert response shape — they assert request routing only.
"""
import pytest
import respx
import httpx

from tests.conftest import SAMPLE_OPPORTUNITY

SAM_URL = "https://api.sam.gov/opportunities/v2/search"

_CANNED = {
    "totalRecords": 1,
    "opportunitiesData": [SAMPLE_OPPORTUNITY],
}


# ---------------------------------------------------------------------------
# Helper: extract the captured SAM.gov request params as a plain dict
# ---------------------------------------------------------------------------
def _captured_params(route) -> dict:
    return dict(route.calls[0].request.url.params)


# ---------------------------------------------------------------------------
# 1. naics_code  →  ncode  (was naicsCode — verified wrong on 2026-06-03)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_naics_filter_sends_ncode(client):
    """naics_code param must reach SAM.gov as 'ncode', NOT 'naicsCode'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get("/api/contracts/search", params={"naics_code": "541512"})
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("ncode") == "541512", (
        f"Expected 'ncode'='541512' in SAM.gov request, got params={p}"
    )
    assert "naicsCode" not in p, (
        "'naicsCode' must NOT be sent to SAM.gov — it is a response field, not a filter param"
    )


# ---------------------------------------------------------------------------
# 2. keyword  →  title  (was q — verified wrong on 2026-06-03)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_keyword_filter_sends_title(client):
    """keyword param must reach SAM.gov as 'title', NOT 'q'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get("/api/contracts/search", params={"keyword": "cybersecurity"})
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("title") == "cybersecurity", (
        f"Expected 'title'='cybersecurity' in SAM.gov request, got params={p}"
    )
    assert "q" not in p, (
        "'q' must NOT be sent to SAM.gov — it is silently ignored by v2 API"
    )


# ---------------------------------------------------------------------------
# 3. set_aside  →  typeOfSetAside  (verified correct on 2026-06-03)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_set_aside_filter_sends_typeOfSetAside(client):
    """set_aside param must reach SAM.gov as 'typeOfSetAside'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get("/api/contracts/search", params={"set_aside": "SDVOSBC"})
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("typeOfSetAside") == "SDVOSBC", (
        f"Expected 'typeOfSetAside'='SDVOSBC', got params={p}"
    )


# ---------------------------------------------------------------------------
# 4. agency  →  organizationName  (verified correct on 2026-06-03)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agency_filter_sends_organizationName(client):
    """agency param must reach SAM.gov as 'organizationName'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get("/api/contracts/search", params={"agency": "Army"})
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("organizationName") == "Army", (
        f"Expected 'organizationName'='Army', got params={p}"
    )


# ---------------------------------------------------------------------------
# 5. solicitation_type  →  ptype  (verified correct on 2026-06-03)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_solicitation_type_filter_sends_ptype(client):
    """solicitation_type param must reach SAM.gov as 'ptype'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get("/api/contracts/search", params={"solicitation_type": "o"})
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("ptype") == "o", (
        f"Expected 'ptype'='o', got params={p}"
    )


# ---------------------------------------------------------------------------
# 6. state  →  placeOfPerformanceState  (confirmed in CLAUDE.md)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_state_filter_sends_placeOfPerformanceState(client):
    """state param must reach SAM.gov as 'placeOfPerformanceState'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get("/api/contracts/search", params={"state": "TX"})
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("placeOfPerformanceState") == "TX", (
        f"Expected 'placeOfPerformanceState'='TX', got params={p}"
    )


# ---------------------------------------------------------------------------
# 7. posted_from  →  postedFrom  (confirmed in CLAUDE.md)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_posted_from_filter_sends_postedFrom(client):
    """posted_from param must reach SAM.gov as 'postedFrom'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get(
            "/api/contracts/search",
            params={"posted_from": "01/01/2025", "posted_to": "06/01/2025"},
        )
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("postedFrom") == "01/01/2025", (
        f"Expected 'postedFrom'='01/01/2025', got params={p}"
    )


# ---------------------------------------------------------------------------
# 8. posted_to  →  postedTo  (confirmed in CLAUDE.md)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_posted_to_filter_sends_postedTo(client):
    """posted_to param must reach SAM.gov as 'postedTo'."""
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=_CANNED)
        )
        r = await client.get(
            "/api/contracts/search",
            params={"posted_from": "01/01/2025", "posted_to": "06/30/2025"},
        )
    assert r.status_code == 200
    p = _captured_params(route)
    assert p.get("postedTo") == "06/30/2025", (
        f"Expected 'postedTo'='06/30/2025', got params={p}"
    )
