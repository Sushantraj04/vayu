import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Index
from backend.app.core.database import Base


class FireEvent(Base):
    __tablename__ = "fire_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String(100), unique=True, index=True, nullable=True) # e.g. viirs_snpp_lat_lon_time
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    brightness_temp_k = Column(Float, nullable=True)
    frp_mw = Column(Float, nullable=False, default=0.0) # Fire Radiative Power (MW)
    acquisition_time = Column(DateTime(timezone=True), nullable=False, index=True)
    confidence = Column(String(20), nullable=True, default="nominal") # nominal, low, high
    satellite = Column(String(50), nullable=False, default="VIIRS_SNPP")
    day_night = Column(String(5), nullable=True, default="D") # D, N
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_fire_coords_time", "latitude", "longitude", "acquisition_time"),
    )

    def __repr__(self):
        return f"<FireEvent ({self.latitude}, {self.longitude}) FRP={self.frp_mw}MW at {self.acquisition_time}>"
