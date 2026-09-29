import asyncio
from celery.utils.log import get_task_logger
from backend.app.worker import celery_app
from backend.app.core.database import AsyncSessionLocal
from backend.app.ingestion.openaq import sync_station_telemetry
from backend.app.ingestion.firms import sync_active_fires
from backend.app.ingestion.openmeteo import sync_corridor_weather
from backend.app.ingestion.gibs import GibsLayerVerifier

logger = get_task_logger(__name__)


def run_async(coro):
    """Utility to run an async coroutine inside a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def task_sync_openaq(self):
    """Periodic Celery task for OpenAQ station telemetry."""
    logger.info("Starting OpenAQ station telemetry sync...")
    async def _run():
        async with AsyncSessionLocal() as db:
            return await sync_station_telemetry(db)
    try:
        count = run_async(_run())
        logger.info(f"OpenAQ sync complete. Ingested {count} readings.")
        return {"status": "success", "count": count}
    except Exception as exc:
        logger.error(f"OpenAQ sync failed: {exc}. Retrying...")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def task_sync_firms(self):
    """Periodic Celery task for NASA FIRMS VIIRS active fires."""
    logger.info("Starting NASA FIRMS VIIRS active fire sync...")
    async def _run():
        async with AsyncSessionLocal() as db:
            return await sync_active_fires(db, days=1)
    try:
        count = run_async(_run())
        logger.info(f"NASA FIRMS sync complete. Ingested {count} fire events.")
        return {"status": "success", "count": count}
    except Exception as exc:
        logger.error(f"NASA FIRMS sync failed: {exc}. Retrying...")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def task_sync_weather(self):
    """Periodic Celery task for Open-Meteo wind and boundary layer weather."""
    logger.info("Starting Open-Meteo weather sync...")
    async def _run():
        async with AsyncSessionLocal() as db:
            return await sync_corridor_weather(db)
    try:
        count = run_async(_run())
        logger.info(f"Weather sync complete. Updated {count} snapshots.")
        return {"status": "success", "count": count}
    except Exception as exc:
        logger.error(f"Weather sync failed: {exc}. Retrying...")
        raise self.retry(exc=exc)


@celery_app.task
def task_verify_gibs():
    """Periodic check of NASA GIBS tile capabilities."""
    logger.info("Verifying NASA GIBS WMTS capabilities...")
    async def _run():
        return await GibsLayerVerifier.verify_capabilities()
    result = run_async(_run())
    logger.info(f"GIBS verification result: {result.get('is_operational')}")
    return result
