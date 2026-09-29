import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from backend.app.ingestion.quality import (
    PhysicalRangeValidator, 
    calculate_cpcb_naqi, 
    check_sensor_staleness,
    SourceStatusTracker
)


# 1. Math & Range Quality Tests
def test_physical_range_validator():
    # Valid
    is_valid, _ = PhysicalRangeValidator.validate("pm25", 85.0)
    assert is_valid is True

    # Invalid negative
    is_valid, reason = PhysicalRangeValidator.validate("pm25", -5.0)
    assert is_valid is False
    assert "bounds" in reason.lower()

    # Invalid extreme spike
    is_valid, reason = PhysicalRangeValidator.validate("pm25", 3500.0)
    assert is_valid is False


def test_cpcb_naqi_calculation():
    # Good (0-30 -> 0-50)
    aqi, cat = calculate_cpcb_naqi(15.0)
    assert aqi <= 50
    assert cat == "Good"

    # Satisfactory (31-60 -> 51-100)
    aqi, cat = calculate_cpcb_naqi(45.0)
    assert 51 <= aqi <= 100
    assert cat == "Satisfactory"

    # Moderate (61-90 -> 101-200)
    aqi, cat = calculate_cpcb_naqi(75.0)
    assert 101 <= aqi <= 200
    assert cat == "Moderate"

    # Poor (91-120 -> 201-300)
    aqi, cat = calculate_cpcb_naqi(105.0)
    assert 201 <= aqi <= 300
    assert cat == "Poor"

    # Very Poor (121-250 -> 301-400)
    aqi, cat = calculate_cpcb_naqi(185.0)
    assert 301 <= aqi <= 400
    assert cat == "Very Poor"

    # Severe (251+ -> 401-500)
    aqi, cat = calculate_cpcb_naqi(350.0)
    assert aqi >= 401
    assert cat == "Severe"


def test_sensor_staleness_detector():
    # Active
    readings = [45.0, 48.0, 52.0, 49.0, 55.0, 60.0]
    now = datetime.now(timezone.utc)
    is_stale, _ = check_sensor_staleness(readings, now)
    assert is_stale is False

    # Flatline (zero variance)
    flatline = [50.0, 50.0, 50.0, 50.0, 50.0, 50.0]
    is_stale, reason = check_sensor_staleness(flatline, now)
    assert is_stale is True
    assert "flatline" in reason.lower()

    # Latency > 2 hours
    old_time = now - timedelta(hours=3)
    is_stale, reason = check_sensor_staleness(readings, old_time)
    assert is_stale is True
    assert "lag exceeds" in reason.lower()


# 2. API Integration Tests
@pytest.mark.asyncio
async def test_stations_and_readings_api(async_client: AsyncClient):
    # 1. List stations
    resp = await async_client.get("/api/v1/stations/")
    assert resp.status_code == 200
    stations = resp.json()
    assert len(stations) >= 1
    stn_id = stations[0]["id"]

    # 2. Get readings with data origin validation
    r_resp = await async_client.get(f"/api/v1/stations/{stn_id}/readings")
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data["count"] >= 2
    origins = [r["data_origin"] for r in r_data["readings"]]
    assert "MEASURED" in origins
    assert "MODELLED" in origins


@pytest.mark.asyncio
async def test_fires_and_weather_api(async_client: AsyncClient):
    # Active fires
    f_resp = await async_client.get("/api/v1/fires/?hours=24")
    assert f_resp.status_code == 200
    f_data = f_resp.json()
    assert f_data["count"] >= 1
    assert f_data["fires"][0]["frp_mw"] == 125.4

    # Weather snapshots
    w_resp = await async_client.get("/api/v1/weather/?city=Delhi-NCR")
    assert w_resp.status_code == 200
    w_data = w_resp.json()
    assert len(w_data) >= 1
    assert w_data[0]["wind_speed_10m_kmh"] == 12.5


@pytest.mark.asyncio
async def test_sources_status_and_federated_status(async_client: AsyncClient):
    # Sources Status (Measured vs Modelled declared)
    s_resp = await async_client.get("/api/v1/sources/status")
    assert s_resp.status_code == 200
    sources = s_resp.json()
    source_types = {s["source_id"]: s["type"] for s in sources}
    assert source_types["openaq"] == "MEASURED"
    assert source_types["firms"] == "MEASURED"
    assert source_types["openmeteo"] == "MODELLED"

    # Federated Status
    fed_resp = await async_client.get("/api/v1/federated/status")
    assert fed_resp.status_code == 200
    fed_data = fed_resp.json()
    assert fed_data["coordinator_status"] == "OPERATIONAL"
    assert "never leaves the node" in fed_data["privacy_contract"]
    assert fed_data["nodes_count"] >= 3


@pytest.mark.asyncio
async def test_alerts_and_cap_xml_export(async_client: AsyncClient):
    # List alerts
    a_resp = await async_client.get("/api/v1/alerts/")
    assert a_resp.status_code == 200
    alerts = a_resp.json()
    assert len(alerts) >= 1
    cap_id = alerts[0]["cap_identifier"]

    # Export CAP 1.2 XML
    cap_resp = await async_client.get(f"/api/v1/alerts/cap/{cap_id}")
    assert cap_resp.status_code == 200
    assert "application/xml" in cap_resp.headers["content-type"]
    assert "urn:oasis:names:tc:emergency:cap:1.2" in cap_resp.text
