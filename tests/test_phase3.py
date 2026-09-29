import pytest
import io
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from PIL import Image

from backend.app.models.station import Station
from backend.app.models.reading import StationReading
from backend.app.models.fire import FireEvent
from backend.app.models.hotspot import Hotspot
from backend.app.models.forecast import Forecast
from backend.app.models.report import CitizenReport
from backend.app.models.alert import Alert

from backend.app.services.citizen_reports import CitizenReportService
from backend.app.analytics.alert_rules import AlertRuleEngine
from backend.app.notifications.dispatcher import CAPFormatter


# ==============================================================================
# 1. Citizen Privacy & Image Sanitization Unit Tests
# ==============================================================================

def test_coordinate_anonymization():
    raw_lat, raw_lon = 28.613912, 77.209043
    pub_lat, pub_lon = CitizenReportService.anonymize_coordinates(raw_lat, raw_lon)

    # Must be rounded to ~500m grid (0.005)
    assert pub_lat == 28.615
    assert pub_lon == 77.21
    assert pub_lat != raw_lat
    assert pub_lon != raw_lon


def test_image_sanitization_strips_metadata():
    # Create test image in memory
    img = Image.new("RGB", (100, 100), color=(200, 50, 50))
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    raw_bytes = img_io.getvalue()

    sanitized_bytes, clean_fn = CitizenReportService.process_and_sanitize_image(raw_bytes, "test_smoke.jpg")

    assert clean_fn.endswith(".jpg")
    assert len(sanitized_bytes) > 0

    # Verify sanitized image can be read and has no EXIF
    clean_img = Image.open(io.BytesIO(sanitized_bytes))
    assert clean_img.format == "JPEG"
    assert clean_img.getexif() == {}


# ==============================================================================
# 2. CAP 1.2 XML & Atom Feed Generation Tests
# ==============================================================================

def test_cap_12_xml_formatting():
    alert = Alert(
        id="test-alert-cap-01",
        cap_identifier="urn:oid:2.49.0.0.356.vayu.2026.TEST01",
        corridor_id="indo-gangetic-main",
        city="Delhi-NCR",
        severity="SEVERE",
        title_en="Severe Air Pollution Inflow",
        title_hi="गंभीर वायु प्रदूषण का प्रवेश",
        description_en="High PM2.5 detected across Delhi-NCR monitoring stations.",
        description_hi="दिल्ली-एनसीआर में अत्यधिक प्रदूषण स्तर दर्ज किया गया।",
        evidence={"pm25": 285.0},
        rule_trigger="SUSTAINED_HIGH_AQI",
        status="NEW",
        created_at=datetime.now(timezone.utc)
    )

    cap_xml = CAPFormatter.to_cap_xml(alert)
    assert 'xmlns="urn:oasis:names:tc:emergency:cap:1.2"' in cap_xml
    assert alert.cap_identifier in cap_xml
    assert "en-IN" in cap_xml
    assert "hi-IN" in cap_xml
    assert alert.title_en in cap_xml
    assert alert.title_hi in cap_xml


def test_cap_atom_feed_generation():
    alert = Alert(
        id="test-alert-feed-01",
        cap_identifier="urn:oid:2.49.0.0.356.vayu.2026.FEED01",
        corridor_id="indo-gangetic-main",
        city="Ludhiana",
        severity="CRITICAL",
        title_en="Critical Crop Burning Cluster",
        title_hi="गंभीर पराली दहन चेतावनी",
        description_en="Extensive active fire clusters detected.",
        description_hi="सक्रिय पराली दहन क्लस्टर दर्ज।",
        evidence={},
        rule_trigger="CORRIDOR_TRANS_BOUNDARY",
        status="NEW",
        created_at=datetime.now(timezone.utc)
    )

    feed_xml = CAPFormatter.to_atom_feed([alert])
    assert 'xmlns="http://www.w3.org/2005/Atom"' in feed_xml
    assert "VAYU-NET Digital Public Good" in feed_xml
    assert alert.cap_identifier in feed_xml


# ==============================================================================
# 3. Phase 3 API Integration Endpoints Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_citizen_report_submission_and_anti_spam(async_client: AsyncClient):
    # 1. First submission should succeed
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "category": "smoke",
        "user_pm25": 145.0,
        "consent": True
    }
    resp1 = await async_client.post("/api/v1/reports/json", json=payload)
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["status"] == "success"
    assert "public_id" in data1
    assert data1["public_lat"] == 28.615
    assert data1["public_lon"] == 77.21

    # 2. Duplicate submission immediately from same client should trigger 429 anti-spam
    resp2 = await async_client.post("/api/v1/reports/json", json=payload)
    assert resp2.status_code == 429
    assert "Duplicate submission" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_citizen_report_list_api(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/reports/")
    assert resp.status_code == 200
    reports = resp.json()
    assert isinstance(reports, list)
    if reports:
        # Verify that only public rounded coordinates are exposed
        r = reports[0]
        assert "public_lat" in r
        assert "public_lon" in r
        assert "raw_lat" not in r
        assert "raw_lon" not in r


@pytest.mark.asyncio
async def test_alert_rule_evaluation_and_atom_feed_api(async_client: AsyncClient):
    # Trigger rule evaluation
    eval_resp = await async_client.post("/api/v1/alerts/evaluate")
    assert eval_resp.status_code == 201
    eval_data = eval_resp.json()
    assert "count" in eval_data

    # Query CAP Atom feed
    feed_resp = await async_client.get("/api/v1/alerts/feed.atom")
    assert feed_resp.status_code == 200
    assert "application/atom+xml" in feed_resp.headers["content-type"]
    assert "urn:oasis:names:tc:emergency:cap:1.2" in feed_resp.text or "VAYU-NET" in feed_resp.text


@pytest.mark.asyncio
async def test_alert_acknowledgement_rbac(async_client: AsyncClient):
    # Get seeded alert from conftest
    list_resp = await async_client.get("/api/v1/alerts/")
    assert list_resp.status_code == 200
    alerts = list_resp.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    # Login as admin to acknowledge
    admin_login = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@vayu-net.org",
        "password": "AdminPassword123!"
    })
    token = admin_login.json()["access_token"]

    ack_resp = await async_client.put(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["alert_status"] == "ACKNOWLEDGED"
