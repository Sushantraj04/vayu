import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Index
from backend.app.core.database import Base


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    city = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature_2m_c = Column(Float, nullable=True)
    relative_humidity_2m_pct = Column(Float, nullable=True)
    wind_speed_10m_kmh = Column(Float, nullable=False, default=0.0)
    wind_direction_10m_deg = Column(Float, nullable=False, default=0.0)
    boundary_layer_height_m = Column(Float, nullable=True)
    surface_pressure_hpa = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_weather_city_timestamp", "city", "timestamp", unique=True),
    )

    def __repr__(self):
        return f"<WeatherSnapshot city={self.city} time={self.timestamp} wind={self.wind_speed_10m_kmh}km/h@{self.wind_direction_10m_deg}°>"
