import time
from datetime import datetime, timezone
from typing import List, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.weather import WeatherSnapshot
from backend.app.ingestion.quality import PhysicalRangeValidator, SourceStatusTracker

OPENMETEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


async def sync_corridor_weather(db: AsyncSession) -> int:
    """
    Ingests hourly wind vectors, temperature, humidity, surface pressure, and boundary layer height (BLH)
    for all configured cities along the corridor.
    """
    start_time = time.time()
    corridors_cfg = settings.get_corridors_config()
    snapshots_added = 0
    errors: List[str] = []

    # Collect unique cities and coordinates
    cities_map: Dict[str, Dict[str, float]] = {}
    for c in corridors_cfg.get("corridors", []):
        for node in c.get("nodes", []):
            cities_map[node["city"]] = {"lat": node["lat"], "lon": node["lon"]}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for city, coords in cities_map.items():
            try:
                params = {
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure",
                    "hourly": "boundary_layer_height",
                    "forecast_days": 1,
                    "timezone": "UTC"
                }
                resp = await client.get(OPENMETEO_WEATHER_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get("current", {})
                    hourly = data.get("hourly", {})
                    
                    # Boundary layer height for current hour
                    blh_values = hourly.get("boundary_layer_height", [])
                    current_blh = blh_values[0] if blh_values else None

                    now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

                    # Check if snapshot exists
                    stmt = select(WeatherSnapshot).where(
                        WeatherSnapshot.city == city,
                        WeatherSnapshot.timestamp == now_utc
                    )
                    existing = (await db.execute(stmt)).scalar_one_or_none()

                    temp = current.get("temperature_2m")
                    humidity = current.get("relative_humidity_2m")
                    wind_speed = current.get("wind_speed_10m", 0.0)
                    wind_dir = current.get("wind_direction_10m", 0.0)
                    pressure = current.get("surface_pressure")

                    if not existing:
                        snapshot = WeatherSnapshot(
                            city=city,
                            latitude=coords["lat"],
                            longitude=coords["lon"],
                            timestamp=now_utc,
                            temperature_2m_c=temp,
                            relative_humidity_2m_pct=humidity,
                            wind_speed_10m_kmh=wind_speed,
                            wind_direction_10m_deg=wind_dir,
                            boundary_layer_height_m=current_blh,
                            surface_pressure_hpa=pressure
                        )
                        db.add(snapshot)
                        snapshots_added += 1
                    else:
                        existing.temperature_2m_c = temp
                        existing.relative_humidity_2m_pct = humidity
                        existing.wind_speed_10m_kmh = wind_speed
                        existing.wind_direction_10m_deg = wind_dir
                        existing.boundary_layer_height_m = current_blh
                        existing.surface_pressure_hpa = pressure

            except Exception as e:
                errors.append(f"{city}: {str(e)}")

    await db.commit()
    latency = (time.time() - start_time) * 1000
    SourceStatusTracker.record_sync(
        "openmeteo", 
        snapshots_added, 
        latency, 
        errors[0] if errors and snapshots_added == 0 else None
    )
    logger.info(f"Synchronized weather for {len(cities_map)} corridor cities in {latency:.1f}ms")
    return snapshots_added
