import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.database import AsyncSessionLocal
from backend.app.ingestion.openmeteo import sync_corridor_weather
from backend.app.ingestion.openaq import sync_station_telemetry
from backend.app.models.station import Station
from backend.app.models.reading import StationReading
from backend.app.models.weather import WeatherSnapshot
from sqlalchemy import select, desc


async def main():
    print("=" * 60)
    print("  Running Live Telemetry & Weather Sync for all Cities")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        print("\n[*] 1. Syncing live atmospheric weather from Open-Meteo...")
        w_count = await sync_corridor_weather(db)
        print(f"    -> Weather snapshots updated: {w_count}")

        print("\n[*] 2. Syncing live station telemetry (OpenAQ / Open-Meteo)...")
        r_count = await sync_station_telemetry(db)
        print(f"    -> Station readings ingested: {r_count}")

        print("\n=== LATEST WEATHER PER CITY ===")
        stmt_w = select(WeatherSnapshot).order_by(desc(WeatherSnapshot.timestamp))
        snapshots = (await db.execute(stmt_w)).scalars().all()
        seen_cities = set()
        for s in snapshots:
            if s.city not in seen_cities:
                seen_cities.add(s.city)
                print(f"City: {s.city:<15} | Wind: {s.wind_speed_10m_kmh:>5.1f} km/h @ {s.wind_direction_10m_deg:>3.0f}° | BLH: {s.boundary_layer_height_m}m | Temp: {s.temperature_2m_c}°C")

        print("\n=== LATEST PM2.5 / AQI READINGS PER CITY ===")
        stmt_stn = select(Station)
        stations = (await db.execute(stmt_stn)).scalars().all()
        for stn in stations:
            stmt_r = (
                select(StationReading)
                .where(StationReading.station_id == stn.id, StationReading.parameter == "pm25")
                .order_by(desc(StationReading.timestamp))
                .limit(1)
            )
            r = (await db.execute(stmt_r)).scalar_one_or_none()
            if r:
                print(f"City: {stn.city:<15} | Station: {stn.name:<30} | PM2.5: {r.value:>5.1f} µg/m³ | AQI: {r.aqi_value} ({r.aqi_category}) | Origin: {r.data_origin}")
            else:
                print(f"City: {stn.city:<15} | Station: {stn.name:<30} | NO PM2.5 READING")

if __name__ == "__main__":
    asyncio.run(main())
