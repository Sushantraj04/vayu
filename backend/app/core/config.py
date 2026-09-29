import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core App
    PROJECT_NAME: str = "VAYU-NET"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "vayu-net-insecure-dev-secret-key-change-in-production-12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vayunet_local.db"
    SYNC_DATABASE_URL: str = "sqlite:///./vayunet_local.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "vayunet-citizen-reports"

    # External APIs
    FIRMS_MAP_KEY: str = ""
    OPENAQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Alert Dispatch Channels
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "alerts@vayu-net.org"
    EMAILS_FROM_NAME: str = "VAYU-NET Air Alert Network"

    # Privacy & Retention
    REPORT_GEO_ROUNDING_PRECISION: float = 0.005 # ~500m grid
    REPORT_RETENTION_DAYS: int = 90

    # Federated Network
    FL_COORDINATOR_URL: str = "http://localhost:8005"
    FL_NODE_ID: str = "node-delhi"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CONFIG_DIR: Path = BASE_DIR / "config"

    def get_corridors_config(self) -> Dict[str, Any]:
        """Loads declarative corridor configs from YAML."""
        config_path = self.CONFIG_DIR / "corridors.yaml"
        if not config_path.exists():
            return {"corridors": []}
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_aqi_breakpoints(self) -> Dict[str, Any]:
        """Loads AQI breakpoints from YAML."""
        config_path = self.CONFIG_DIR / "aqi_breakpoints.yaml"
        if not config_path.exists():
            return {"schemes": {}}
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


settings = Settings()
