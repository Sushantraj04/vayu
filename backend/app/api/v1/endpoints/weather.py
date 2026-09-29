from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.weather import WeatherSnapshot

router = APIRouter()


@router.get("/")
async def list_weather_snapshots(
    city: Optional[str] = Query(None, description="Filter by city name"),
    limit: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns atmospheric boundary layer, wind vector, and thermodynamic snapshots
    from Open-Meteo along the corridor.
    """
    stmt = select(WeatherSnapshot)
    if city:
        stmt = stmt.where(WeatherSnapshot.city == city)
    stmt = stmt.order_by(desc(WeatherSnapshot.timestamp)).limit(limit)

    snapshots = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": w.id,
            "city": w.city,
            "latitude": w.latitude,
            "longitude": w.longitude,
            "timestamp": w.timestamp,
            "temperature_2m_c": w.temperature_2m_c,
            "relative_humidity_2m_pct": w.relative_humidity_2m_pct,
            "wind_speed_10m_kmh": w.wind_speed_10m_kmh,
            "wind_direction_10m_deg": w.wind_direction_10m_deg,
            "boundary_layer_height_m": w.boundary_layer_height_m,
            "surface_pressure_hpa": w.surface_pressure_hpa,
        }
        for w in snapshots
    ]
