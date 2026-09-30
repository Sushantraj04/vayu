import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.station import Station
from backend.app.models.reading import StationReading
from backend.app.ingestion.quality import PhysicalRangeValidator, calculate_cpcb_naqi, SourceStatusTracker

OPENAQ_BASE_URL = "https://api.openaq.org/v3"
OPENMETEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


async def fetch_openaq_stations(bbox: Dict[str, float]) -> List[Dict[str, Any]]:
    """Fetches reference monitoring stations within the corridor bounding box."""
    if not settings.OPENAQ_API_KEY:
        logger.warning("OPENAQ_API_KEY not configured. Falling back to configured corridor stations.")
        return []

    headers = {"X-API-Key": settings.OPENAQ_API_KEY}
    params = {
        "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}",
        "limit": 100,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OPENAQ_BASE_URL}/locations", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
    except Exception as e:
        logger.error(f"OpenAQ API station fetch failed: {str(e)}")
        return []


CITY_OPENAQ_MAP = {
    "delhi-ncr": 13,
    "delhi": 13,
    "ludhiana": 5569,
    "ambala": 6964,
    "agra": 860,
    "kanpur": 5662,
    "lucknow": 2456,
}


async def sync_station_telemetry(db: AsyncSession) -> int:
    """
    Ingests live PM2.5 and PM10 readings for corridor stations.
    Pulls real MEASURED CPCB sensor telemetry from OpenAQ v3 when available.
    If OpenAQ is sparse or unavailable, falls back to Open-Meteo Air Quality
    with mandatory DATA_ORIGIN: MODELLED tagging.
    """
    start_time = time.time()
    corridors_cfg = settings.get_corridors_config()
    readings_count = 0
    errors: List[str] = []

    # Get registered stations
    stmt = select(Station).where(Station.is_active == True)
    stations = (await db.execute(stmt)).scalars().all()

    async with httpx.AsyncClient(timeout=12.0) as client:
        for stn in stations:
            synced = False

            # 1. Attempt OpenAQ pull if configured
            loc_id = None
            if stn.external_id and stn.external_id.startswith("openaq_"):
                loc_id = stn.external_id.replace("openaq_", "")
            elif stn.city:
                loc_id = CITY_OPENAQ_MAP.get(stn.city.lower()) or CITY_OPENAQ_MAP.get(stn.city.lower().replace("-ncr", ""))

            if settings.OPENAQ_API_KEY and loc_id:
                try:
                    headers = {"X-API-Key": settings.OPENAQ_API_KEY}
                    resp = await client.get(
                        f"{OPENAQ_BASE_URL}/locations/{loc_id}/sensors",
                        headers=headers
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        for s in results:
                            param = s.get("parameter", {}).get("name", "").lower()
                            latest = s.get("latest") or {}
                            val = latest.get("value")
                            unit = s.get("parameter", {}).get("units", "ug/m3")

                            if param in ["pm25", "pm10"] and val is not None:
                                is_valid, _ = PhysicalRangeValidator.validate(param, val)
                                if is_valid:
                                    now_utc = datetime.now(timezone.utc)
                                    aqi_val, aqi_cat = calculate_cpcb_naqi(val) if param == "pm25" else (None, None)
                                    
                                    reading = StationReading(
                                        station_id=stn.id,
                                        timestamp=now_utc,
                                        parameter=param,
                                        value=round(val, 1),
                                        unit=unit,
                                        aqi_value=aqi_val,
                                        aqi_category=aqi_cat,
                                        data_origin="MEASURED"
                                    )
                                    db.add(reading)
                                    readings_count += 1
                                    synced = True

                        if synced:
                            stn.data_source = "OpenAQ CPCB Reference"
                            stn.last_sync = datetime.now(timezone.utc)
                            stn.is_stale = False
                except Exception as e:
                    errors.append(f"OpenAQ {stn.city}: {str(e)}")

            # 2. Fallback to Open-Meteo Air Quality (Clearly tagged MODELLED)
            if not synced:
                try:
                    params = {
                        "latitude": stn.latitude,
                        "longitude": stn.longitude,
                        "current": "pm2_5,pm10",
                        "timezone": "UTC"
                    }
                    resp = await client.get(OPENMETEO_AQ_URL, params=params)
                    if resp.status_code == 200:
                        curr = resp.json().get("current", {})
                        pm25_val = curr.get("pm2_5")
                        pm10_val = curr.get("pm10")
                        now_utc = datetime.now(timezone.utc)

                        if pm25_val is not None:
                            is_valid, _ = PhysicalRangeValidator.validate("pm25", pm25_val)
                            if is_valid:
                                aqi_val, aqi_cat = calculate_cpcb_naqi(pm25_val)
                                r_pm25 = StationReading(
                                    station_id=stn.id,
                                    timestamp=now_utc,
                                    parameter="pm25",
                                    value=pm25_val,
                                    unit="ug/m3",
                                    aqi_value=aqi_val,
                                    aqi_category=aqi_cat,
                                    data_origin="MODELLED" # Explicitly labeled
                                )
                                db.add(r_pm25)
                                readings_count += 1

                        if pm10_val is not None:
                            is_valid, _ = PhysicalRangeValidator.validate("pm10", pm10_val)
                            if is_valid:
                                r_pm10 = StationReading(
                                    station_id=stn.id,
                                    timestamp=now_utc,
                                    parameter="pm10",
                                    value=pm10_val,
                                    unit="ug/m3",
                                    aqi_value=None,
                                    aqi_category=None,
                                    data_origin="MODELLED"
                                )
                                db.add(r_pm10)
                                readings_count += 1

                        stn.last_sync = now_utc
                        stn.is_stale = False
                except Exception as e:
                    errors.append(f"OpenMeteo Fallback {stn.city}: {str(e)}")

    await db.commit()
    latency = (time.time() - start_time) * 1000
    SourceStatusTracker.record_sync(
        "openaq", 
        readings_count, 
        latency, 
        errors[0] if errors and readings_count == 0 else None
    )
    logger.info(f"Synchronized {readings_count} station readings in {latency:.1f}ms")
    return readings_count
