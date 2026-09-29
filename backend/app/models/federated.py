import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from backend.app.core.database import Base


class FederatedRound(Base):
    __tablename__ = "federated_rounds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    round_number = Column(Integer, unique=True, index=True, nullable=False)
    coordinator_version = Column(String(50), nullable=False)
    participating_nodes = Column(JSON, nullable=False) # ["node-ludhiana", "node-delhi", "node-lucknow"]
    global_loss = Column(Float, nullable=False)
    weight_divergence = Column(Float, nullable=False)
    weights_s3_key = Column(String(255), nullable=True)
    status = Column(String(30), default="COMPLETED", nullable=False)
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<FederatedRound #{self.round_number} Loss={self.global_loss:.4f} Nodes={len(self.participating_nodes)}>"
