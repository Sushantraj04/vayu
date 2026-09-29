from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.database import get_db
from backend.app.models.hotspot import Hotspot
from backend.app.models.fire import FireEvent
from backend.app.models.reading import StationReading
from backend.app.models.station import Station
from backend.app.models.report import CitizenReport
from backend.app.analytics.hotspots import HotspotDetectionEngine
from backend.app.core.config import settings
import yaml

router = APIRouter()


@router.get("/")
async def list_hotspots(
    corridor_id: Optional[str] = Query(None, description="Filter by corridor ID"),
    is_active: bool = Query(True, description="Filter active clusters"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns spatial pollution hotspots detected via DBSCAN clustering
    with attached plain-language physical source attribution.
    """
    stmt = select(Hotspot).where(Hotspot.is_active == is_active)
    if corridor_id:
        stmt = stmt.where(Hotspot.corridor_id == corridor_id)
    stmt = stmt.order_by(desc(Hotspot.detected_at))

    hotspots = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": h.id,
            "corridor_id": h.corridor_id,
            "centroid_lat": h.centroid_lat,
            "centroid_lon": h.centroid_lon,
            "radius_km": h.radius_km,
            "cluster_size": h.cluster_size,
            "mean_pm25": h.mean_pm25,
            "max_frp_mw": h.max_frp_mw,
            "probable_source": h.probable_source,
            "reasoning": h.reasoning,
            "evidence": h.evidence,
            "severity": h.severity,
            "detected_at": h.detected_at,
            "is_active": h.is_active,
        }
        for h in hotspots
    ]


@router.post("/detect", status_code=status.HTTP_201_CREATED)
async def trigger_hotspot_detection(
    hours: int = Query(24, description="Lookback window in hours for fires and anomalies"),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes DBSCAN spatio-temporal clustering over real active fire radiometry,
    anomalous ground station telemetry, and recent citizen reports.
    Persists resulting clusters to the Hotspot database.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # 1. Fetch recent active fires
    f_stmt = select(FireEvent).where(FireEvent.acquisition_time >= since)
    fires = (await db.execute(f_stmt)).scalars().all()

    # 2. Fetch ground station readings with elevated PM2.5 (>= 90 ug/m3)
    r_stmt = (
        select(Station, StationReading)
        .join(StationReading, Station.id == StationReading.station_id)
        .where(StationReading.timestamp >= since)
        .where(StationReading.parameter == "pm25")
        .where(StationReading.value >= 90.0)
    )
    stn_pairs = (await db.execute(r_stmt)).all()

    # 3. Fetch recent citizen reports
    rep_stmt = select(CitizenReport).where(CitizenReport.created_at >= since)
    reports = (await db.execute(rep_stmt)).scalars().all()

    # 4. Load corridors config for spine assignment
    corridors_cfg = settings.get_corridors_config().get("corridors", [])

    # 5. Run DBSCAN clustering
    engine = HotspotDetectionEngine(eps_km=35.0, min_samples=2)
    detected_hotspots = engine.cluster_points(
        fires=fires,
        anomalous_readings=stn_pairs,
        citizen_reports=reports,
        corridors_config=corridors_cfg
    )

    # 6. Deactivate old active hotspots and insert new ones
    old_stmt = select(Hotspot).where(Hotspot.is_active == True)
    old_hotspots = (await db.execute(old_stmt)).scalars().all()
    for old in old_hotspots:
        old.is_active = False

    for h in detected_hotspots:
        db.add(h)

    await db.commit()

    return {
        "message": f"DBSCAN clustering executed. {len(detected_hotspots)} hotspots detected and persisted.",
        "count": len(detected_hotspots),
        "hotspots": [
            {
                "id": h.id,
                "centroid_lat": h.centroid_lat,
                "centroid_lon": h.centroid_lon,
                "radius_km": h.radius_km,
                "cluster_size": h.cluster_size,
                "probable_source": h.probable_source,
                "severity": h.severity,
                "reasoning": h.reasoning,
                "evidence": h.evidence
            }
            for h in detected_hotspots
        ]
    }
