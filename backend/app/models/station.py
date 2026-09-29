import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Index
from backend.app.core.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation_m = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    data_source = Column(String(50), nullable=False, default="OPENAQ") # OPENAQ, CPCB, OPENMETEO
    is_stale = Column(Boolean, default=False, nullable=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_station_coords", "latitude", "longitude"),
        Index("idx_station_city_active", "city", "is_active"),
    )

    def __repr__(self):
        return f"<Station {self.name} ({self.city})>"
