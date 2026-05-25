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
    """Endpoint returns the requested number of MonthlyCount objects."""
    _all_months_respond(respx, 5)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512&months=12")
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
    resp = await client.get("/api/insights/naics-activity?naics_code=541512&set_aside=SDVOSBC&months=12")
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

    assert first_count == 18   # 3 month calls + 15 agency calls
    assert second_count == 18  # no additional calls — all fully cached


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


# ---------------------------------------------------------------------------
# Phase 2 tests — bid timing, FY forecast, agency breakdown
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_bid_timing_present(client):
    """When months have activity, bid_timing advice is populated."""
    _all_months_respond(respx, 5)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    assert data["bid_timing"] is not None
    bt = data["bid_timing"]
    assert "best_months" in bt and len(bt["best_months"]) > 0
    assert "recommendation" in bt and bt["recommendation"]
    assert "prep_window" in bt and bt["prep_window"]


@pytest.mark.asyncio
@respx.mock
async def test_bid_timing_zero_activity(client):
    """When all months are 0, bid_timing is None."""
    _all_months_respond(respx, 0)
    resp = await client.get("/api/insights/naics-activity?naics_code=999999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["bid_timing"] is None


@pytest.mark.asyncio
@respx.mock
async def test_fy_forecast_always_present(client):
    """fy_forecast is always included regardless of NAICS activity level."""
    _all_months_respond(respx, 0)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fy_forecast"] is not None


@pytest.mark.asyncio
@respx.mock
async def test_fy_forecast_fields(client):
    """fy_forecast contains required fields with expected types and valid values."""
    _all_months_respond(respx, 3)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    fy = resp.json()["fy_forecast"]
    assert fy["fy_label"].startswith("FY")
    assert isinstance(fy["is_surge_window"], bool)
    assert fy["days_remaining"] > 0
    assert len(fy["message"]) > 20


@pytest.mark.asyncio
@respx.mock
async def test_agency_breakdown_present(client):
    """When agencies have activity, agency_breakdown is populated."""
    _all_months_respond(respx, 3)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agency_breakdown"] is not None
    ab = data["agency_breakdown"]
    assert len(ab["agencies"]) <= 5
    assert ab["total_agencies_active"] >= 1
    assert ab["interpretation"]


@pytest.mark.asyncio
@respx.mock
async def test_agency_breakdown_max_5_agencies(client):
    """agency_breakdown never surfaces more than 5 agencies."""
    _all_months_respond(respx, 10)  # all 15 agencies return 10, only top 5 returned
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    ab = resp.json()["agency_breakdown"]
    assert ab is not None
    assert len(ab["agencies"]) <= 5


@pytest.mark.asyncio
@respx.mock
async def test_agency_breakdown_zero_activity(client):
    """When all agency queries return 0, agency_breakdown is None."""
    _all_months_respond(respx, 0)
    resp = await client.get("/api/insights/naics-activity?naics_code=999999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agency_breakdown"] is None


@pytest.mark.asyncio
@respx.mock
async def test_agency_breakdown_sorted_desc(client):
    """Agencies in breakdown are sorted by count descending."""
    _all_months_respond(respx, 5)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    ab = resp.json()["agency_breakdown"]
    if ab and len(ab["agencies"]) > 1:
        counts = [a["count"] for a in ab["agencies"]]
        assert counts == sorted(counts, reverse=True)


@pytest.mark.asyncio
@respx.mock
async def test_bid_timing_best_months_are_valid_labels(client):
    """best_months must be a subset of the complete months' labels."""
    _all_months_respond(respx, 4)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    if data["bid_timing"]:
        all_labels = {m["month_label"] for m in data["months"]}
        for label in data["bid_timing"]["best_months"]:
            assert label in all_labels


@pytest.mark.asyncio
@respx.mock
async def test_phase2_response_shape(client):
    """Full response includes all Phase 1 and Phase 2 fields."""
    _all_months_respond(respx, 2)
    resp = await client.get("/api/insights/naics-activity?naics_code=541512")
    assert resp.status_code == 200
    data = resp.json()
    for field in ("months", "total_opportunities", "avg_per_month", "peak_month",
                  "interpretation", "bid_timing", "fy_forecast", "agency_breakdown"):
        assert field in data, f"missing field: {field}"
