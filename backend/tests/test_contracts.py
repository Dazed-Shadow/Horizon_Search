import json
import pytest
import respx
import httpx
from tests.conftest import SAMPLE_SAM_RESPONSE, SAMPLE_OPPORTUNITY


SAM_URL = "https://api.sam.gov/opportunities/v2/search"


@pytest.mark.asyncio
async def test_search_returns_results(client):
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_SAM_RESPONSE)
        )
        r = await client.get("/api/contracts/search", params={"keyword": "IT support"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["contracts"]) >= 1
    contract = data["contracts"][0]
    assert contract["notice_id"] == "abc123"
    assert contract["set_aside_code"] == "SDVOSBC"


@pytest.mark.asyncio
async def test_open_only_filters_awards(client):
    """open_only=true (default) should drop award notice type contracts."""
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_SAM_RESPONSE)
        )
        r = await client.get("/api/contracts/search", params={"open_only": "true"})
    assert r.status_code == 200
    types = [c["solicitation_type"] for c in r.json()["contracts"]]
    assert "a" not in types


@pytest.mark.asyncio
async def test_open_only_false_shows_awards(client):
    """open_only=false should include award notices."""
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_SAM_RESPONSE)
        )
        r = await client.get("/api/contracts/search", params={"open_only": "false"})
    assert r.status_code == 200
    types = [c["solicitation_type"] for c in r.json()["contracts"]]
    assert "a" in types


@pytest.mark.asyncio
async def test_search_with_veteran_set_aside(client):
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={
                "totalRecords": 1,
                "opportunitiesData": [SAMPLE_OPPORTUNITY],
            })
        )
        r = await client.get("/api/contracts/search", params={"set_aside": "SDVOSBC"})
    assert r.status_code == 200
    assert r.json()["contracts"][0]["set_aside_code"] == "SDVOSBC"


@pytest.mark.asyncio
async def test_search_empty_results(client):
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"totalRecords": 0, "opportunitiesData": []})
        )
        r = await client.get("/api/contracts/search")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["contracts"] == []


@pytest.mark.asyncio
async def test_search_sam_gov_400(client):
    """SAM.gov returning 400 → our API returns 502."""
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(return_value=httpx.Response(400))
        r = await client.get("/api/contracts/search")
    assert r.status_code == 502


@pytest.mark.asyncio
async def test_search_sam_gov_500(client):
    """SAM.gov returning 500 → our API returns 502."""
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(return_value=httpx.Response(500))
        r = await client.get("/api/contracts/search")
    assert r.status_code == 502


@pytest.mark.asyncio
async def test_search_malformed_sam_response(client):
    """SAM.gov returning unexpected structure — should not cause a 500."""
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"unexpected": "format"})
        )
        r = await client.get("/api/contracts/search")
    assert r.status_code == 200
    assert r.json()["contracts"] == []


@pytest.mark.asyncio
async def test_search_string_total(client):
    """SAM.gov sometimes returns totalRecords as a string — should coerce cleanly."""
    with respx.mock as mock:
        mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={
                "totalRecords": "42",
                "opportunitiesData": [],
            })
        )
        r = await client.get("/api/contracts/search")
    assert r.status_code == 200
    assert r.json()["total"] == 42


@pytest.mark.asyncio
async def test_pagination_params(client):
    with respx.mock as mock:
        route = mock.route(url__startswith=SAM_URL).mock(
            return_value=httpx.Response(200, json={"totalRecords": 0, "opportunitiesData": []})
        )
        r = await client.get("/api/contracts/search", params={"limit": 10, "offset": 20})
    assert r.status_code == 200
    called_params = dict(route.calls[0].request.url.params)
    assert called_params["limit"] == "10"
    assert called_params["offset"] == "20"


@pytest.mark.asyncio
async def test_limit_max_capped(client):
    """limit > 100 should be rejected by FastAPI validation."""
    r = await client.get("/api/contracts/search", params={"limit": 999})
    assert r.status_code == 422
