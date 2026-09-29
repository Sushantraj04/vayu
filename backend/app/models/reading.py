import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index
from backend.app.core.database import Base


class StationReading(Base):
    __tablename__ = "station_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    station_id = Column(String(36), ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    parameter = Column(String(20), nullable=False, default="pm25", index=True) # pm25, pm10, no2, so2, o3, co
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False, default="ug/m3")
    aqi_value = Column(Integer, nullable=True)
    aqi_category = Column(String(50), nullable=True) # Good, Satisfactory, Moderate, Poor, Very Poor, Severe
    data_origin = Column(String(20), nullable=False, default="MEASURED") # MEASURED, MODELLED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_reading_station_time_param", "station_id", "timestamp", "parameter", unique=True),
        Index("idx_reading_time_origin", "timestamp", "data_origin"),
    )

    def __repr__(self):
        return f"<StationReading station={self.station_id} {self.parameter}={self.value} {self.unit} ({self.data_origin})>"
