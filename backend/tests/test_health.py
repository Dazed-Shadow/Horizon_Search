import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_config_status_no_key(client, monkeypatch):
    monkeypatch.setenv("SAM_GOV_API_KEY", "")
    r = await client.get("/api/config/status")
    assert r.status_code == 200
    data = r.json()
    assert data["api_key_configured"] is False


@pytest.mark.asyncio
async def test_config_status_with_key(client, monkeypatch):
    monkeypatch.setenv("SAM_GOV_API_KEY", "SAM-fake-key-12345")
    r = await client.get("/api/config/status")
    assert r.status_code == 200
    data = r.json()
    assert data["api_key_configured"] is True


@pytest.mark.asyncio
async def test_filter_set_asides(client):
    r = await client.get("/api/contracts/filters/set-asides")
    assert r.status_code == 200
    codes = [item["code"] for item in r.json()]
    assert "SDVOSBC" in codes
    assert "VSB" in codes
    assert "8AN" in codes


@pytest.mark.asyncio
async def test_filter_solicitation_types(client):
    r = await client.get("/api/contracts/filters/solicitation-types")
    assert r.status_code == 200
    codes = [item["code"] for item in r.json()]
    assert "o" in codes   # Solicitation
    assert "r" in codes   # Sources Sought
    assert "a" in codes   # Award Notice
