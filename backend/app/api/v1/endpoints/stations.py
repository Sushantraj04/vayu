from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.station import Station
from backend.app.models.reading import StationReading

router = APIRouter()


@router.get("/")
async def list_stations(
    city: Optional[str] = Query(None, description="Filter by city name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    data_source: Optional[str] = Query(None, description="Filter by data source (OPENAQ, CPCB, OPENMETEO)"),
    db: AsyncSession = Depends(get_db)
):
    """Lists air quality reference stations across the corridor bounding box."""
    stmt = select(Station).where(Station.is_active == True)
    if city:
        stmt = stmt.where(Station.city == city)
    if state:
        stmt = stmt.where(Station.state == state)
    if data_source:
        stmt = stmt.where(Station.data_source == data_source)

    stations = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": s.id,
            "external_id": s.external_id,
            "name": s.name,
            "city": s.city,
            "state": s.state,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "elevation_m": s.elevation_m,
            "data_source": s.data_source,
            "is_stale": s.is_stale,
            "last_sync": s.last_sync,
        }
        for s in stations
    ]


@router.get("/{station_id}/readings")
async def get_station_readings(
    station_id: str,
    parameter: str = Query("pm25", description="Pollutant parameter (pm25, pm10)"),
    limit: int = Query(48, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns time-series pollutant readings for a station.
    Every reading includes truthful DATA_ORIGIN tag: MEASURED or MODELLED.
    """
    # Verify station exists
    stn_stmt = select(Station).where(Station.id == station_id)
    station = (await db.execute(stn_stmt)).scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    stmt = (
        select(StationReading)
        .where(
            StationReading.station_id == station_id,
            StationReading.parameter == parameter
        )
        .order_by(desc(StationReading.timestamp))
        .limit(limit)
    )
    readings = (await db.execute(stmt)).scalars().all()

    return {
        "station_id": station.id,
        "station_name": station.name,
        "city": station.city,
        "parameter": parameter,
        "count": len(readings),
        "readings": [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "value": r.value,
                "unit": r.unit,
                "aqi_value": r.aqi_value,
                "aqi_category": r.aqi_category,
                "data_origin": r.data_origin # Transparently tells whether sensor or modelled
            }
            for r in readings
        ]
    }
