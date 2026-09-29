from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.fire import FireEvent

router = APIRouter()


@router.get("/")
async def list_active_fires(
    hours: int = Query(24, ge=1, le=72, description="Lookback window in hours (default 24h, max 72h)"),
    min_frp: float = Query(0.0, ge=0.0, description="Minimum Fire Radiative Power (MW)"),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns active fire pixels from NASA FIRMS VIIRS 375m sensor.
    Bounded to Indo-Gangetic corridor: lat [25.5°N - 32.0°N], lon [73.0°E - 82.0°E].
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    stmt = (
        select(FireEvent)
        .where(
            FireEvent.acquisition_time >= cutoff,
            FireEvent.frp_mw >= min_frp
        )
        .order_by(desc(FireEvent.acquisition_time))
        .limit(limit)
    )
    fires = (await db.execute(stmt)).scalars().all()

    return {
        "count": len(fires),
        "lookback_hours": hours,
        "source": "NASA FIRMS VIIRS 375m (SNPP/NOAA-20)",
        "fires": [
            {
                "id": f.id,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "frp_mw": f.frp_mw,
                "brightness_temp_k": f.brightness_temp_k,
                "acquisition_time": f.acquisition_time,
                "confidence": f.confidence,
                "satellite": f.satellite,
                "day_night": f.day_night
            }
            for f in fires
        ]
    }
