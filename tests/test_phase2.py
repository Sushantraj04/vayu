import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
import numpy as np

from backend.app.models.hotspot import Hotspot
from backend.app.models.fire import FireEvent
from backend.app.models.reading import StationReading
from backend.app.models.station import Station
from backend.app.models.weather import WeatherSnapshot
from backend.app.models.report import CitizenReport

from backend.app.analytics.hotspots import HotspotDetectionEngine, haversine_km
from backend.app.analytics.attribution import (
    KinematicSourceAttributionEngine, 
    calculate_bearing_deg, 
    compass_direction_name
)
from backend.app.analytics.forecaster import CityAirQualityForecaster
from backend.app.analytics.registry import ModelRegistryService


# ==============================================================================
# 1. Hotspot Clustering Tests (DBSCAN)
# ==============================================================================

def test_haversine_and_bearing_calculations():
    # Delhi to Ludhiana (~290 km, bearing ~325 deg NW)
    delhi_lat, delhi_lon = 28.6139, 77.2090
    ludhiana_lat, ludhiana_lon = 30.9010, 75.8573

    dist = haversine_km(delhi_lat, delhi_lon, ludhiana_lat, ludhiana_lon)
    assert 280.0 <= dist <= 310.0

    bearing = calculate_bearing_deg(delhi_lat, delhi_lon, ludhiana_lat, ludhiana_lon)
    assert 315.0 <= bearing <= 335.0
    assert compass_direction_name(bearing) in ["NW", "NNW"]


def test_hotspot_dbscan_clustering_engine():
    now = datetime.now(timezone.utc)
    engine = HotspotDetectionEngine(eps_km=35.0, min_samples=2)

    # 3 active fires clustered tightly in Sangrur/Ludhiana district
    fires = [
        FireEvent(
            id="f1",
            latitude=30.90,
            longitude=75.85,
            frp_mw=85.0,
            confidence="high",
            acquisition_time=now
        ),
        FireEvent(
            id="f2",
            latitude=30.95,
            longitude=75.88,
            frp_mw=120.0,
            confidence="high",
            acquisition_time=now
        ),
        FireEvent(
            id="f3",
            latitude=30.88,
            longitude=75.82,
            frp_mw=65.0,
            confidence="high",
            acquisition_time=now
        ),
        # 1 isolated distant low-FRP fire (should be filtered or outlier)
        FireEvent(
            id="f4_distant",
            latitude=26.50,
            longitude=83.50,
            frp_mw=15.0,
            confidence="nominal",
            acquisition_time=now
        )
    ]

    stn = Station(id="stn_test", name="Ludhiana Monitor", city="Ludhiana", latitude=30.92, longitude=75.86)
    reading = StationReading(station_id="stn_test", value=195.0, parameter="pm25", timestamp=now)
    anomalous = [(stn, reading)]

    hotspots = engine.cluster_points(
        fires=fires,
        anomalous_readings=anomalous,
        citizen_reports=[]
    )

    assert len(hotspots) >= 1
    main_cluster = hotspots[0]

    assert main_cluster.cluster_size >= 3
    assert main_cluster.probable_source == "Agricultural Biomass Burning"
    assert main_cluster.severity in ["SEVERE", "CRITICAL"]
    assert main_cluster.max_frp_mw >= 120.0
    assert "Active crop residue fires detected" in main_cluster.reasoning
    assert 30.8 <= main_cluster.centroid_lat <= 31.0
    assert 75.8 <= main_cluster.centroid_lon <= 75.9


# ==============================================================================
# 2. Kinematic Source Attribution Tests
# ==============================================================================

def test_kinematic_source_attribution_upwind_vs_downwind():
    engine = KinematicSourceAttributionEngine(dispersion_scale_km=180.0)

    # Receptor: Delhi
    delhi_lat, delhi_lon = 28.6139, 77.2090

    # Hotspot 1: UPWIND in Punjab (NW ~320 deg from Delhi)
    upwind_hotspot = Hotspot(
        id="h_upwind",
        centroid_lat=30.90,
        centroid_lon=75.85,
        probable_source="Agricultural Biomass Burning",
        severity="CRITICAL",
        mean_pm25=220.0,
        evidence={"total_frp_mw": 850.0},
        reasoning="Punjab cluster"
    )

    # Hotspot 2: DOWNWIND in Agra (SE ~135 deg from Delhi)
    downwind_hotspot = Hotspot(
        id="h_downwind",
        centroid_lat=27.18,
        centroid_lon=78.01,
        probable_source="Industrial Cluster",
        severity="SEVERE",
        mean_pm25=180.0,
        evidence={"total_frp_mw": 500.0},
        reasoning="Agra cluster"
    )

    # Meteorological condition: Strong NW wind (315 deg) blowing towards SE
    res = engine.attribute(
        receptor_name="Delhi-NCR",
        receptor_lat=delhi_lat,
        receptor_lon=delhi_lon,
        wind_speed_kmh=15.0,
        wind_direction_deg=315.0, # NW wind
        boundary_layer_height_m=300.0, # Low nocturnal boundary layer
        hotspots=[upwind_hotspot, downwind_hotspot]
    )

    assert res.dominant_source_name == "Agricultural Biomass Burning"
    assert res.confidence_pct >= 60
    assert "Delhi-NCR" in res.plain_language_reasoning
    assert "NW winds" in res.plain_language_reasoning

    # Verify that the upwind source received significant share
    upwind_entry = next((s for s in res.sources if s["hotspot_id"] == "h_upwind"), None)
    assert upwind_entry is not None
    assert upwind_entry["alignment_factor"] > 0.8
    assert upwind_entry["share_pct"] > 40.0

    # Verify downwind source has zero alignment and is not attributed
    downwind_entry = next((s for s in res.sources if s["hotspot_id"] == "h_downwind"), None)
    assert downwind_entry is None or downwind_entry["share_pct"] < 2.0


# ==============================================================================
# 3. Forecaster & Strict Data Integrity Gate Tests
# ==============================================================================

def test_forecaster_insufficient_data_guard():
    forecaster = CityAirQualityForecaster(city="Delhi-NCR")

    # Only 5 hours of readings (far below 48h required)
    now = datetime.now(timezone.utc)
    thin_readings = [
        StationReading(
            station_id="stn_1",
            timestamp=now - timedelta(hours=i),
            parameter="pm25",
            value=120.0 + i
        )
        for i in range(5)
    ]

    forecasts = forecaster.generate_forecasts(
        readings=thin_readings,
        weather_snapshots=[]
    )

    assert len(forecasts) == 3 # 24h, 48h, 72h
    for fc in forecasts:
        assert fc.is_insufficient_data is True
        assert fc.predicted_pm25 is None
        assert fc.predicted_aqi is None
        assert fc.aqi_category == "INSUFFICIENT_DATA"


def test_forecaster_sufficient_data_produces_real_predictions():
    forecaster = CityAirQualityForecaster(city="Delhi-NCR")
    now = datetime.now(timezone.utc)

    # Provide 72 consecutive hours of realistic readings
    readings = []
    weather_snaps = []
    for i in range(72, 0, -1):
        t = now - timedelta(hours=i)
        # Realistic diurnal pattern
        val = 110.0 + 35.0 * np.sin(i * np.pi / 12.0)
        readings.append(StationReading(station_id="stn_1", timestamp=t, parameter="pm25", value=val))
        weather_snaps.append(WeatherSnapshot(
            city="Delhi-NCR",
            timestamp=t,
            temperature_2m_c=22.0,
            relative_humidity_2m_pct=65.0,
            wind_speed_10m_kmh=12.0,
            wind_direction_10m_deg=310.0,
            boundary_layer_height_m=450.0
        ))

    forecasts = forecaster.generate_forecasts(readings=readings, weather_snapshots=weather_snaps, now=now)

    assert len(forecasts) == 3
    for fc in forecasts:
        assert fc.is_insufficient_data is False
        assert fc.predicted_pm25 is not None
        assert fc.predicted_pm25 > 0
        assert fc.predicted_aqi is not None
        assert fc.predicted_aqi > 0
        assert fc.aqi_category in ["Moderate", "Poor", "Very Poor", "Severe"]
        assert fc.lower_bound_pm25 is not None
        assert fc.upper_bound_pm25 is not None
        assert fc.lower_bound_pm25 <= fc.predicted_pm25 <= fc.upper_bound_pm25


# ==============================================================================
# 4. Model Registry & Evaluation Service Tests
# ==============================================================================

def test_model_registry_evaluation_metrics_and_hashing():
    y_true = np.array([120.0, 135.0, 140.0, 155.0, 160.0])
    y_pred = np.array([122.0, 130.0, 142.0, 150.0, 165.0])
    y_base = np.array([115.0, 120.0, 135.0, 140.0, 155.0])

    metrics = ModelRegistryService.evaluate_predictions(y_true, y_pred, y_base)
    assert metrics["mae"] > 0
    assert metrics["rmse"] >= metrics["mae"]
    assert "r2" in metrics
    assert "baseline_mae" in metrics
    assert "skill_score_pct" in metrics

    # Deterministic SHA-256 hash
    h1 = ModelRegistryService.calculate_data_hash([12.5, 14.2, 18.9])
    h2 = ModelRegistryService.calculate_data_hash([12.5, 14.2, 18.9])
    h3 = ModelRegistryService.calculate_data_hash([12.5, 14.2, 19.0])
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


# ==============================================================================
# 5. Phase 2 API Integration Endpoints Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_hotspot_detection_api(async_client: AsyncClient):
    # Trigger DBSCAN clustering endpoint
    resp = await async_client.post("/api/v1/hotspots/detect?hours=48")
    assert resp.status_code == 201
    data = resp.json()
    assert "hotspots" in data
    assert "count" in data

    # Query active hotspots
    list_resp = await async_client.get("/api/v1/hotspots/")
    assert list_resp.status_code == 200
    hotspots = list_resp.json()
    assert isinstance(hotspots, list)


@pytest.mark.asyncio
async def test_source_attribution_api(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/attribution/?city=Delhi-NCR")
    assert resp.status_code == 200
    data = resp.json()

    assert data["receptor"]["name"] == "Delhi-NCR"
    assert "meteorology" in data
    assert "wind_speed_kmh" in data["meteorology"]
    assert "dominant_source" in data
    assert "plain_language_reasoning" in data
    assert 0 <= data["confidence_pct"] <= 100
    assert 0 <= data["local_share_pct"] <= 100


@pytest.mark.asyncio
async def test_forecast_generate_and_list_api(async_client: AsyncClient):
    # On-demand forecast generation (seeded DB only has 2 readings, so must trigger insufficient_data guard)
    gen_resp = await async_client.post("/api/v1/forecasts/generate?city=Delhi-NCR")
    assert gen_resp.status_code == 201
    gen_data = gen_resp.json()
    assert gen_data["is_insufficient_data"] is True
    assert len(gen_data["forecasts"]) == 3
    assert gen_data["forecasts"][0]["aqi_category"] == "INSUFFICIENT_DATA"

    # List forecasts
    list_resp = await async_client.get("/api/v1/forecasts/?city=Delhi-NCR")
    assert list_resp.status_code == 200
    fc_list = list_resp.json()
    assert len(fc_list) >= 3


@pytest.mark.asyncio
async def test_model_registry_api(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/models/")
    assert resp.status_code == 200
    models = resp.json()
    assert isinstance(models, list)
