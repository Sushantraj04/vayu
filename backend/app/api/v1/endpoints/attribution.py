from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.database import get_db
from backend.app.models.hotspot import Hotspot
from backend.app.models.weather import WeatherSnapshot
from backend.app.analytics.attribution import KinematicSourceAttributionEngine

router = APIRouter()

# Default corridor anchor coordinates
CITY_COORDINATES = {
    "Delhi-NCR": (28.6139, 77.2090),
    "Ludhiana": (30.9010, 75.8573),
    "Ambala": (30.3782, 76.7767),
    "Agra": (27.1767, 78.0081),
    "Kanpur": (26.4499, 80.3319),
    "Lucknow": (26.8467, 80.9462),
}


@router.get("/")
async def get_source_attribution(
    city: str = Query("Delhi-NCR", description="Target city for attribution analysis"),
    lat: Optional[float] = Query(None, description="Optional custom receptor latitude"),
    lon: Optional[float] = Query(None, description="Optional custom receptor longitude"),
    db: AsyncSession = Depends(get_db)
):
    """
    Computes heuristic kinematic atmospheric source attribution for a target city or coordinate.
    Calculates upwind angular deviation from current wind vector, exponential distance decay,
    and nocturnal boundary layer compression to apportion pollution sources.
    """
    if lat is not None and lon is not None:
        rec_lat, rec_lon = lat, lon
        rec_name = f"Receptor ({lat:.2f}, {lon:.2f})"
    elif city in CITY_COORDINATES:
        rec_lat, rec_lon = CITY_COORDINATES[city]
        rec_name = city
    else:
        # Default to Delhi-NCR coordinates if unknown
        rec_lat, rec_lon = CITY_COORDINATES["Delhi-NCR"]
        rec_name = city

    # 1. Fetch latest weather for receptor city
    w_stmt = (
        select(WeatherSnapshot)
        .where(WeatherSnapshot.city == city)
        .order_by(desc(WeatherSnapshot.timestamp))
        .limit(1)
    )
    weather = (await db.execute(w_stmt)).scalars().first()

    if not weather:
        # Check any weather snapshot
        w_any_stmt = select(WeatherSnapshot).order_by(desc(WeatherSnapshot.timestamp)).limit(1)
        weather = (await db.execute(w_any_stmt)).scalars().first()

    wind_speed = weather.wind_speed_10m_kmh if weather else 12.0
    wind_deg = weather.wind_direction_10m_deg if weather else 315.0
    blh = weather.boundary_layer_height_m if weather else 400.0

    # 2. Fetch active hotspots
    h_stmt = select(Hotspot).where(Hotspot.is_active == True)
    hotspots = (await db.execute(h_stmt)).scalars().all()

    # 3. Execute Kinematic Attribution Engine
    engine = KinematicSourceAttributionEngine(dispersion_scale_km=180.0, base_local_emission_factor=2.5)
    result = engine.attribute(
        receptor_name=rec_name,
        receptor_lat=rec_lat,
        receptor_lon=rec_lon,
        wind_speed_kmh=wind_speed,
        wind_direction_deg=wind_deg,
        boundary_layer_height_m=blh,
        hotspots=hotspots
    )

    return {
        "receptor": {
            "name": result.receptor_name,
            "latitude": result.receptor_lat,
            "longitude": result.receptor_lon,
        },
        "meteorology": {
            "wind_speed_kmh": result.wind_speed_kmh,
            "wind_direction_deg": result.wind_direction_deg,
            "wind_direction_cardinal": result.wind_direction_cardinal,
            "boundary_layer_height_m": result.boundary_layer_height_m,
        },
        "dominant_source": result.dominant_source_name,
        "confidence_pct": result.confidence_pct,
        "local_share_pct": result.local_share_pct,
        "attributed_sources": result.sources,
        "plain_language_reasoning": result.plain_language_reasoning,
    }
