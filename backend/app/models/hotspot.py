import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Index
from backend.app.core.database import Base


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    corridor_id = Column(String(100), nullable=True, index=True)
    centroid_lat = Column(Float, nullable=False, index=True)
    centroid_lon = Column(Float, nullable=False, index=True)
    radius_km = Column(Float, nullable=False, default=15.0)
    cluster_size = Column(Integer, nullable=False, default=1)
    mean_pm25 = Column(Float, nullable=True)
    max_frp_mw = Column(Float, nullable=False, default=0.0)
    
    # Probable source: Agricultural burning, Industrial, Traffic-Dust, Trans-boundary
    probable_source = Column(String(100), nullable=False, default="Unclassified")
    reasoning = Column(String(500), nullable=False) # Plain-language explanation
    evidence = Column(JSON, nullable=False) # {fire_count, distance_to_fire_km, wind_alignment_deg, blh_m, station_anomaly_z}
    severity = Column(String(50), nullable=False, default="MODERATE") # MODERATE, HIGH, SEVERE, CRITICAL
    
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        Index("idx_hotspot_active_detected", "is_active", "detected_at"),
    )

    def __repr__(self):
        return f"<Hotspot ({self.centroid_lat}, {self.centroid_lon}) Source={self.probable_source} Severity={self.severity}>"
