from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.corridor import Corridor, CorridorSummary, CorridorNode
from backend.app.models.station import Station
from backend.app.models.reading import StationReading
from backend.app.models.fire import FireEvent
from backend.app.models.alert import Alert

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def list_corridors():
    """
    Returns all configured economic and transport corridors.
    Configuration-driven via corridors.yaml.
    """
    config = settings.get_corridors_config()
    return config.get("corridors", [])


@router.get("/{corridor_id}", response_model=Dict[str, Any])
async def get_corridor_detail(corridor_id: str):
    """
    Returns detailed node-chain geometry for a specified corridor.
    """
    config = settings.get_corridors_config()
    for corridor in config.get("corridors", []):
        if corridor["id"] == corridor_id:
            return corridor
    raise HTTPException(status_code=404, detail=f"Corridor '{corridor_id}' not found")


@router.get("/{corridor_id}/summary", response_model=CorridorSummary)
async def get_corridor_summary(
    corridor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Computes real-time operational summary and Corridor Risk Index (CRI).
    Zero fake data: if no station telemetry exists, values are truthfully None / Insufficient.
    """
    config = settings.get_corridors_config()
    selected = None
    for corridor in config.get("corridors", []):
        if corridor["id"] == corridor_id:
            selected = corridor
            break
            
    if not selected:
        raise HTTPException(status_code=404, detail=f"Corridor '{corridor_id}' not found")

    # Fetch active alerts for corridor
    alert_count_stmt = select(func.count(Alert.id)).where(
        Alert.corridor_id == corridor_id,
        Alert.status.in_(["NEW", "ACKNOWLEDGED"])
    )
    active_alerts = (await db.execute(alert_count_stmt)).scalar() or 0

    # Fetch active fires in bounding box
    bbox = selected.get("bounding_box", {})
    fire_count_stmt = select(func.count(FireEvent.id)).where(
        FireEvent.latitude >= bbox.get("min_lat", 0),
        FireEvent.latitude <= bbox.get("max_lat", 90),
        FireEvent.longitude >= bbox.get("min_lon", 0),
        FireEvent.longitude <= bbox.get("max_lon", 180),
    )
    active_fires = (await db.execute(fire_count_stmt)).scalar() or 0

    nodes_summary: List[CorridorNode] = []
    worst_city_now = None
    worst_aqi_now = None
    max_pm25_val = 0.0

    for n in selected.get("nodes", []):
        # Query latest reading for city
        stmt = (
            select(StationReading)
            .join(Station, Station.id == StationReading.station_id)
            .where(Station.city == n["city"], StationReading.parameter == "pm25")
            .order_by(desc(StationReading.timestamp))
            .limit(1)
        )
        latest_reading = (await db.execute(stmt)).scalar_one_or_none()

        curr_pm25 = latest_reading.value if latest_reading else None
        curr_aqi = latest_reading.aqi_value if latest_reading else None
        aqi_cat = latest_reading.aqi_category if latest_reading else "Insufficient Data"

        if curr_pm25 and curr_pm25 > max_pm25_val:
            max_pm25_val = curr_pm25
            worst_city_now = n["city"]
            worst_aqi_now = curr_aqi

        nodes_summary.append(
            CorridorNode(
                city=n["city"],
                state=n["state"],
                lat=n["lat"],
                lon=n["lon"],
                order=n["order"],
                is_hub=n.get("is_hub", False),
                fl_node_id=n.get("fl_node_id"),
                fl_port=n.get("fl_port"),
                elevation_m=n.get("elevation_m"),
                current_pm25=curr_pm25,
                current_aqi=curr_aqi,
                aqi_category=aqi_cat
            )
        )

    # Compute Corridor Risk Index (CRI 0-100)
    # Formula: 0.40*(max_pm25/500*100) + 0.25*(forecast_peak/500*100) + 0.20*(fires/100*100) + 0.15*(alerts*10)
    pm25_factor = min(100.0, (max_pm25_val / 500.0) * 100.0)
    fire_factor = min(100.0, (active_fires / 50.0) * 100.0)
    alert_factor = min(100.0, active_alerts * 20.0)
    
    cri = round(0.50 * pm25_factor + 0.30 * fire_factor + 0.20 * alert_factor, 1)
    
    if cri >= 80:
        risk_level = "SEVERE"
    elif cri >= 55:
        risk_level = "HIGH"
    elif cri >= 30:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return CorridorSummary(
        id=selected["id"],
        name=selected["name"],
        code=selected["code"],
        risk_index=cri,
        risk_level=risk_level,
        active_alerts_count=active_alerts,
        active_fires_count=active_fires,
        worst_city_now=worst_city_now or "Awaiting Sensor Data",
        worst_aqi_now=worst_aqi_now,
        worst_city_forecast=None,
        worst_aqi_forecast=None,
        nodes=nodes_summary
    )
