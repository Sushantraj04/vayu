import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Index
from backend.app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    corridor_id = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    severity = Column(String(30), nullable=False, index=True) # MODERATE, HIGH, SEVERE, EMERGENCY
    
    # Bilingual advisory content
    title_en = Column(String(255), nullable=False)
    title_hi = Column(String(255), nullable=False)
    description_en = Column(String(1000), nullable=False)
    description_hi = Column(String(1000), nullable=False)
    
    # Underlying physical evidence
    evidence = Column(JSON, nullable=False) # {trigger_type, threshold, current_value, upwind_fires, forecast_peak}
    rule_trigger = Column(String(100), nullable=False) # FORECAST_SPIKE, UPWIND_FIRE_CLUSTER, SENSOR_OUTAGE, CITIZEN_CLUSTER
    
    # Lifecycle: NEW -> ACKNOWLEDGED -> RESOLVED, EXPIRED
    status = Column(String(30), default="NEW", nullable=False, index=True)
    acknowledged_by = Column(String(36), nullable=True)
    acknowledged_by_email = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolved_by_email = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # OASIS CAP 1.2 Identifier
    cap_identifier = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_alert_status_created", "status", "created_at"),
        Index("idx_alert_corridor_severity", "corridor_id", "severity"),
    )

    def __repr__(self):
        return f"<Alert {self.cap_identifier} [{self.severity}] for {self.city} Status={self.status}>"
