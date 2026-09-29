import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from backend.app.core.database import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String(100), nullable=False) # e.g. "xgboost-ludhiana-pm25", "fedavg-igp-gru"
    version = Column(String(50), nullable=False)
    city = Column(String(100), nullable=True) # None for global federated model
    training_window_start = Column(DateTime(timezone=True), nullable=False)
    training_window_end = Column(DateTime(timezone=True), nullable=False)
    metrics = Column(JSON, nullable=False) # {mae: 18.2, rmse: 24.1, baseline_mae: 32.5, r2: 0.78}
    data_hash = Column(String(64), nullable=False) # SHA-256 hash of training dataset
    status = Column(String(30), default="ACTIVE", nullable=False) # ACTIVE, STAGED, ARCHIVED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<ModelRegistry {self.model_name}:{self.version} ({self.status})>"
