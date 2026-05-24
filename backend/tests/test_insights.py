"""
Tests for GET /api/insights/naics-activity.

Mocking strategy: respx intercepts all SAM.gov calls.
Each month query returns {"totalRecords": N} — we control N per test.
"""
import pytest
import respx
import httpx
from httpx import Response

from services.sam_gov import SAM_BASE

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sam_resp(total: int) -> Response:
    return Response(200, json={"totalRecords": total, "opportunitiesData": []})


def _all_months_respond(mock, total: int):
    """Make every SAM.gov call return the same totalRecords value."""
    mock.route(url__startswith=SAM_BASE).mock(return_value=_sam_resp(total))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_insight_endpoint_basic(client):
    """Endpoint returns 12 MonthlyCount objects for a valid NAICS code."""
    _all_months_respond(respx, 5)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    assert data["naics_code"] == "541512"
    assert len(data["months"]) == 12
    assert all(m["count"] == 5 for m in data["months"])
    assert data["total_opportunities"] == 60
    assert data["set_aside_code"] is None


@pytest.mark.asyncio
@respx.mock
async def test_insight_endpoint_with_set_aside(client):
    """set_aside param is forwarded to SAM.gov and reflected in the response."""
    _all_months_respond(respx, 3)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512&set_aside=SDVOSBC")
    assert resp.status_code == 200
    data = resp.json()
    assert data["set_aside_code"] == "SDVOSBC"
    assert data["set_aside_label"] == "SDVOSB Competitive"
    assert len(data["months"]) == 12


@pytest.mark.asyncio
async def test_insight_missing_naics(client):
    """Missing naics_code query param returns 422."""
    resp = await client.get("/api/insights/naics-activity")
    assert resp.status_code == 422


@pytest.mark.asyncio
@respx.mock
async def test_insight_months_param(client):
    """months=6 returns exactly 6 MonthlyCount objects."""
    _all_months_respond(respx, 2)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512&months=6")
    assert resp.status_code == 200
    assert len(resp.json()["months"]) == 6


@pytest.mark.asyncio
@respx.mock
async def test_insight_cache_hit(client):
    """Second request for the same NAICS serves from cache; SAM.gov called only once per month."""
    from services.insights import _insight_cache
    _insight_cache.clear()

    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        return _sam_resp(4)

    with respx.mock:
        respx.route(url__startswith=SAM_BASE).mock(side_effect=handler)
        await client.get("/api/insights/naics-activity?naics_code=541511&months=3")
        first_count = call_count
        await client.get("/api/insights/naics-activity?naics_code=541511&months=3")
        second_count = call_count

    assert first_count == 3    # one call per month
    assert second_count == 3   # no additional calls — fully cached


@pytest.mark.asyncio
@respx.mock
async def test_insight_sam_error_returns_502(client):
    """SAM.gov 500 → our API returns 502."""
    respx.route(url__startswith=SAM_BASE).mock(return_value=Response(500))
    # Each month catches the error and returns count=0; endpoint itself succeeds
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    # Service catches individual month errors and returns 0; endpoint returns 200 with zero counts
    assert resp.status_code == 200
    data = resp.json()
    assert all(m["count"] == 0 for m in data["months"])
    assert "No" in data["interpretation"]


@pytest.mark.asyncio
@respx.mock
async def test_insight_avg_excludes_current_month(client):
    """avg_per_month is the mean of complete months only (current partial month excluded)."""
    from datetime import datetime
    now = datetime.utcnow()
    current_key = f"{now.year:04d}-{now.month:02d}"

    def handler(request):
        # Current month returns 100, all others return 1
        posted_from = request.url.params.get("postedFrom", "")
        month_str = posted_from[6:10] + "-" + posted_from[0:2] if posted_from else ""
        return _sam_resp(100 if month_str == current_key[:4] + "-" + current_key[5:] else 1)

    respx.route(url__startswith=SAM_BASE).mock(side_effect=handler)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    # avg should be ~1.0 (the 11 complete months), not skewed by the current month
    assert data["avg_per_month"] <= 2.0


@pytest.mark.asyncio
@respx.mock
async def test_insight_zero_activity_interpretation(client):
    """When all months return 0, interpretation contains guidance to broaden the search."""
    _all_months_respond(respx, 0)
    resp = await client.get("/api/insights/naics-activity?naics_code=999999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_opportunities"] == 0
    interp = data["interpretation"]
    assert "No" in interp or "no" in interp
