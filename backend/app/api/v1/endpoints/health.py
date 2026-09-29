from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe: verifies process is alive and receiving traffic."""
    return HealthResponse(
        status="healthy",
        service="vayu-net-backend",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Readiness probe: validates connectivity to PostgreSQL, Redis, and Object Storage.
    """
    db_status = "ok"
    redis_status = "ok"
    minio_status = "ok"

    # 1. Test Database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    # 2. Test Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.5)
        await r.ping()
        await r.close()
    except Exception:
        redis_status = "unavailable"

    # 3. Test MinIO / S3
    try:
        from minio import Minio
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        # Quick non-blocking list check
        client.bucket_exists(settings.MINIO_BUCKET_NAME)
    except Exception:
        minio_status = "unavailable"

    is_ready = db_status == "ok"
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(
        status="ready" if is_ready else "degraded",
        database=db_status,
        redis=redis_status,
        minio=minio_status,
        timestamp=datetime.now(timezone.utc)
    )
