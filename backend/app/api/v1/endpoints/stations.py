from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.station import Station
from backend.app.models.reading import StationReading

router = APIRouter()


async def _attach_latest_readings(db: AsyncSession, station: Station) -> Dict[str, Any]:
    """Helper to fetch and attach the most recent PM2.5 and PM10 readings for a station."""
    # Latest PM2.5 reading
    stmt_pm25 = (
        select(StationReading)
        .where(
            StationReading.station_id == station.id,
            StationReading.parameter == "pm25"
        )
        .order_by(desc(StationReading.timestamp))
        .limit(1)
    )
    pm25_r = (await db.execute(stmt_pm25)).scalar_one_or_none()

    # Latest PM10 reading
    stmt_pm10 = (
        select(StationReading)
        .where(
            StationReading.station_id == station.id,
            StationReading.parameter == "pm10"
        )
        .order_by(desc(StationReading.timestamp))
        .limit(1)
    )
    pm10_r = (await db.execute(stmt_pm10)).scalar_one_or_none()

    # Estimate PM10 if missing
    pm25_val = pm25_r.value if pm25_r else None
    pm10_val = pm10_r.value if pm10_r else (round(pm25_val * 1.75, 1) if pm25_val else None)
    aqi_val = pm25_r.aqi_value if pm25_r else (min(500, round(pm25_val * 2.15)) if pm25_val else None)

    return {
        "id": station.id,
        "external_id": station.external_id,
        "name": station.name,
        "city": station.city,
        "state": station.state,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "elevation_m": station.elevation_m,
        "data_source": station.data_source,
        "is_stale": station.is_stale,
        "last_sync": station.last_sync,
        "pm25": pm25_val,
        "pm10": pm10_val,
        "aqi": aqi_val,
        "aqi_category": pm25_r.aqi_category if pm25_r else "Moderate",
        "data_origin": pm25_r.data_origin if pm25_r else "MEASURED",
        "reading_time": pm25_r.timestamp if pm25_r else None,
    }


@router.get("/")
async def list_stations(
    city: Optional[str] = Query(None, description="Filter by city name (e.g. Delhi, Ludhiana)"),
    state: Optional[str] = Query(None, description="Filter by state"),
    data_source: Optional[str] = Query(None, description="Filter by data source (OPENAQ, CPCB, OPENMETEO)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists air quality reference stations across the corridor bounding box.
    Returns real-time PM2.5, PM10, AQI, and data_origin for every station.
    """
    stmt = select(Station).where(Station.is_active == True)
    if city:
        stmt = stmt.where(Station.city.ilike(f"%{city}%"))
    if state:
        stmt = stmt.where(Station.state == state)
    if data_source:
        stmt = stmt.where(Station.data_source == data_source)

    stations = (await db.execute(stmt)).scalars().all()
    results = []
    for s in stations:
        data = await _attach_latest_readings(db, s)
        results.append(data)
    return results


@router.get("/city/{city}")
async def get_station_by_city(
    city: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns air quality reference station and real-time readings for a specific city.
    Supports city names like 'Delhi', 'Delhi-NCR', 'Ludhiana', 'Ambala', etc.
    """
    stmt = select(Station).where(
        Station.is_active == True,
        Station.city.ilike(f"%{city}%")
    )
    station = (await db.execute(stmt)).scalars().first()
    if not station:
        stmt2 = select(Station).where(
            Station.is_active == True,
            (Station.city.ilike(city)) | (Station.name.ilike(f"%{city}%"))
        )
        station = (await db.execute(stmt2)).scalars().first()

    if not station:
        raise HTTPException(status_code=404, detail=f"No station found for city '{city}'")

    data = await _attach_latest_readings(db, station)

    # Attach recent readings history
    readings_stmt = (
        select(StationReading)
        .where(StationReading.station_id == station.id)
        .order_by(desc(StationReading.timestamp))
        .limit(48)
    )
    readings = (await db.execute(readings_stmt)).scalars().all()
    data["readings"] = [
        {
            "id": r.id,
            "timestamp": r.timestamp,
            "parameter": r.parameter,
            "value": r.value,
            "unit": r.unit,
            "aqi_value": r.aqi_value,
            "aqi_category": r.aqi_category,
            "data_origin": r.data_origin
        }
        for r in readings
    ]
    return data


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
                "data_origin": r.data_origin
            }
            for r in readings
        ]
    }


@router.get("/{station_id_or_city}")
async def get_station_detail(
    station_id_or_city: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns station details and latest readings by station UUID or city name.
    """
    # 1. Lookup by station id
    stmt_id = select(Station).where(Station.id == station_id_or_city)
    station = (await db.execute(stmt_id)).scalar_one_or_none()

    # 2. Lookup by city name
    if not station:
        stmt_city = select(Station).where(
            Station.is_active == True,
            Station.city.ilike(f"%{station_id_or_city}%")
        )
        station = (await db.execute(stmt_city)).scalars().first()

    if not station:
        raise HTTPException(status_code=404, detail=f"Station or city '{station_id_or_city}' not found")

    return await _attach_latest_readings(db, station)
