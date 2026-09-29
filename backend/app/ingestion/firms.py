import csv
import io
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.fire import FireEvent
from backend.app.ingestion.quality import SourceStatusTracker

FIRMS_API_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


async def sync_active_fires(db: AsyncSession, days: int = 1) -> int:
    """
    Ingests active fire pixels from NASA FIRMS VIIRS 375m (SNPP/NOAA-20).
    Filters to corridor bounding box: [25.5°N - 32.0°N, 73.0°E - 82.0°E].
    """
    start_time = time.time()
    
    if not settings.FIRMS_MAP_KEY:
        logger.warning("FIRMS_MAP_KEY not configured. Awaiting user key in .env.")
        SourceStatusTracker.record_sync("firms", 0, 0, "FIRMS_MAP_KEY not set")
        return 0

    # Indo-Gangetic Bounding Box: min_lon,min_lat,max_lon,max_lat
    bbox_str = "73.0,25.5,82.0,32.0"
    url = f"{FIRMS_API_BASE}/{settings.FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/{bbox_str}/{days}"
    
    fires_added = 0
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                err_msg = f"NASA FIRMS API returned status {resp.status_code}: {resp.text[:100]}"
                SourceStatusTracker.record_sync("firms", 0, (time.time() - start_time) * 1000, err_msg)
                logger.error(err_msg)
                return 0

            # Parse CSV response
            csv_file = io.StringIO(resp.text)
            reader = csv.DictReader(csv_file)

            for row in reader:
                try:
                    lat = float(row.get("latitude", 0))
                    lon = float(row.get("longitude", 0))
                    frp = float(row.get("frp", 0.0) or 0.0)
                    bright = float(row.get("bright_ti4", 0.0) or 0.0)
                    acq_date = row.get("acq_date", "") # YYYY-MM-DD
                    acq_time = row.get("acq_time", "") # HHMM
                    confidence = row.get("confidence", "nominal")
                    satellite = row.get("satellite", "VIIRS_SNPP")
                    day_night = row.get("daynight", "D")

                    # Parse timestamp
                    dt_str = f"{acq_date} {acq_time.zfill(4)}"
                    acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
                    ext_id = f"viirs_{lat:.4f}_{lon:.4f}_{acq_date}_{acq_time}"

                    # Check if already exists (idempotency)
                    stmt = select(FireEvent.id).where(FireEvent.external_id == ext_id)
                    exists = (await db.execute(stmt)).scalar_one_or_none()

                    if not exists:
                        fire = FireEvent(
                            external_id=ext_id,
                            latitude=lat,
                            longitude=lon,
                            brightness_temp_k=bright,
                            frp_mw=frp,
                            acquisition_time=acq_dt,
                            confidence=confidence,
                            satellite=satellite,
                            day_night=day_night
                        )
                        db.add(fire)
                        fires_added += 1
                except Exception as row_err:
                    continue

            await db.commit()
            latency = (time.time() - start_time) * 1000
            SourceStatusTracker.record_sync("firms", fires_added, latency)
            logger.info(f"Ingested {fires_added} active fire detections from NASA FIRMS VIIRS")
            return fires_added

    except Exception as e:
        latency = (time.time() - start_time) * 1000
        SourceStatusTracker.record_sync("firms", 0, latency, str(e))
        logger.error(f"NASA FIRMS ingestion failed: {str(e)}")
        return 0
