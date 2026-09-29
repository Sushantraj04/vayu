import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import httpx

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal, async_engine, Base
from backend.app.core.config import settings
from backend.app.models.station import Station
from backend.app.models.reading import StationReading
from backend.app.models.weather import WeatherSnapshot
from backend.app.models.audit import AuditLog
from backend.app.ingestion.quality import PhysicalRangeValidator, calculate_cpcb_naqi

# Historical Air Quality & Weather API from Open-Meteo (Free & No Key Required)
OPENMETEO_ARCHIVE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENMETEO_WEATHER_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


async def backfill_stubble_burning_season(
    start_date: str = "2025-10-15",
    end_date: str = "2025-11-30"
):
    """
    Downloads historical air quality and meteorological observations for the 
    autumn stubble burning season (Oct 15 - Nov 30).
    Real training and evaluation data, not mock data.
    """
    print("=" * 65)
    print("  VAYU-NET: Historical Stubble Burning Season Data Backfill")
    print(f"  Target Window: {start_date} to {end_date}")
    print("=" * 65)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Fetch corridor stations
        stmt = select(Station)
        stations = (await session.execute(stmt)).scalars().all()
        if not stations:
            print("[WARN] No stations found. Please run scripts/seed_data.py first.")
            return

        total_readings = 0
        total_weather = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for stn in stations:
                print(f"\n[*] Backfilling telemetry for {stn.city} ({stn.name})...")
                
                # 1. Fetch Historical Atmospheric Pollution
                try:
                    aq_params = {
                        "latitude": stn.latitude,
                        "longitude": stn.longitude,
                        "start_date": start_date,
                        "end_date": end_date,
                        "hourly": "pm2_5,pm10",
                        "timezone": "UTC"
                    }
                    resp = await client.get(OPENMETEO_ARCHIVE_URL, params=aq_params)
                    if resp.status_code == 200:
                        data = resp.json()
                        hourly = data.get("hourly", {})
                        times = hourly.get("time", [])
                        pm25_series = hourly.get("pm2_5", [])
                        pm10_series = hourly.get("pm10", [])

                        for t_str, p25, p10 in zip(times, pm25_series, pm10_series):
                            if p25 is None and p10 is None:
                                continue

                            obs_time = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
                            
                            # Validate & add PM2.5
                            if p25 is not None:
                                is_valid, _ = PhysicalRangeValidator.validate("pm25", p25)
                                if is_valid:
                                    aqi_val, aqi_cat = calculate_cpcb_naqi(p25)
                                    reading_pm25 = StationReading(
                                        station_id=stn.id,
                                        timestamp=obs_time,
                                        parameter="pm25",
                                        value=p25,
                                        unit="ug/m3",
                                        aqi_value=aqi_val,
                                        aqi_category=aqi_cat,
                                        data_origin="MODELLED" # Historical atmospheric reanalysis
                                    )
                                    session.add(reading_pm25)
                                    total_readings += 1

                            # Validate & add PM10
                            if p10 is not None:
                                is_valid, _ = PhysicalRangeValidator.validate("pm10", p10)
                                if is_valid:
                                    reading_pm10 = StationReading(
                                        station_id=stn.id,
                                        timestamp=obs_time,
                                        parameter="pm10",
                                        value=p10,
                                        unit="ug/m3",
                                        aqi_value=None,
                                        aqi_category=None,
                                        data_origin="MODELLED"
                                    )
                                    session.add(reading_pm10)
                                    total_readings += 1

                        print(f"  [OK] Ingested {len(times)} historical hourly atmospheric intervals.")
                    else:
                        print(f"  [FAIL] Failed to retrieve atmospheric history: HTTP {resp.status_code}")
                except Exception as e:
                    print(f"  [ERR] Exception during air quality backfill: {e}")

                # 2. Fetch Historical Meteorology (Wind & Inversion)
                try:
                    meteo_params = {
                        "latitude": stn.latitude,
                        "longitude": stn.longitude,
                        "start_date": start_date,
                        "end_date": end_date,
                        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure",
                        "timezone": "UTC"
                    }
                    resp_m = await client.get(OPENMETEO_WEATHER_ARCHIVE_URL, params=meteo_params)
                    if resp_m.status_code == 200:
                        m_data = resp_m.json()
                        m_hourly = m_data.get("hourly", {})
                        m_times = m_hourly.get("time", [])
                        temps = m_hourly.get("temperature_2m", [])
                        hums = m_hourly.get("relative_humidity_2m", [])
                        wspeeds = m_hourly.get("wind_speed_10m", [])
                        wdirs = m_hourly.get("wind_direction_10m", [])
                        pressures = m_hourly.get("surface_pressure", [])

                        for t_str, tmp, hum, ws, wd, sp in zip(m_times, temps, hums, wspeeds, wdirs, pressures):
                            obs_time = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
                            snapshot = WeatherSnapshot(
                                city=stn.city,
                                latitude=stn.latitude,
                                longitude=stn.longitude,
                                timestamp=obs_time,
                                temperature_2m_c=tmp,
                                relative_humidity_2m_pct=hum,
                                wind_speed_10m_kmh=ws or 0.0,
                                wind_direction_10m_deg=wd or 0.0,
                                surface_pressure_hpa=sp
                            )
                            session.add(snapshot)
                            total_weather += 1
                        print(f"  [OK] Ingested {len(m_times)} historical meteorological snapshots.")
                except Exception as e:
                    print(f"  [ERR] Exception during weather backfill: {e}")

                await session.commit()

        # Audit event recording backfill completion
        audit = AuditLog(
            action="HISTORICAL_BACKFILL_COMPLETED",
            resource_type="training_dataset",
            resource_id="stubble_season_2025",
            user_email="system@vayu-net.org",
            user_role="system",
            details={
                "start_date": start_date,
                "end_date": end_date,
                "total_readings": total_readings,
                "total_weather_snapshots": total_weather,
                "provenance": "Open-Meteo Reanalysis / CAMS Fallback",
                "notes": "Historical FIRMS VIIRS requires NASA Earthdata archive token; models use boundary meteorology and station lags."
            }
        )
        session.add(audit)
        await session.commit()

    print("\n" + "=" * 65)
    print("  HISTORICAL BACKFILL COMPLETE!")
    print(f"  * Total Air Quality Readings Ingested: {total_readings}")
    print(f"  * Total Meteorological Snapshots:     {total_weather}")
    print("  * Data Provenance: Tagged truthfully as MODELLED")
    print("=" * 65)


if __name__ == "__main__":
    # Backfill default 7 days of historical season data for rapid setup
    asyncio.run(backfill_stubble_burning_season(start_date="2025-11-01", end_date="2025-11-07"))
