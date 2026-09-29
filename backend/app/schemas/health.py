from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: str
    database: str
    redis: str
    minio: str
    timestamp: datetime
