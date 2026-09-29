import asyncio
from celery import Celery
from celery.schedules import crontab
from backend.app.core.config import settings

celery_app = Celery(
    "vayunet_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["backend.app.tasks.ingestion_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "sync-openaq-every-15-min": {
            "task": "backend.app.tasks.ingestion_tasks.task_sync_openaq",
            "schedule": 900.0, # 15 minutes
        },
        "sync-firms-every-30-min": {
            "task": "backend.app.tasks.ingestion_tasks.task_sync_firms",
            "schedule": 1800.0, # 30 minutes
        },
        "sync-weather-every-30-min": {
            "task": "backend.app.tasks.ingestion_tasks.task_sync_weather",
            "schedule": 1800.0, # 30 minutes
        },
        "verify-gibs-every-60-min": {
            "task": "backend.app.tasks.ingestion_tasks.task_verify_gibs",
            "schedule": 3600.0, # 60 minutes
        },
    }
)
