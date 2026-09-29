import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Index
from backend.app.core.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    city = Column(String(100), nullable=False, index=True)
    horizon_hours = Column(Integer, nullable=False, index=True) # 24, 48, 72
    target_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    predicted_pm25 = Column(Float, nullable=True)
    predicted_aqi = Column(Integer, nullable=True)
    aqi_category = Column(String(50), nullable=True)
    lower_bound_pm25 = Column(Float, nullable=True) # 10th percentile
    upper_bound_pm25 = Column(Float, nullable=True) # 90th percentile
    model_version = Column(String(50), nullable=False, default="xgboost-city-v1")
    is_insufficient_data = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_forecast_city_horizon_time", "city", "horizon_hours", "target_timestamp"),
    )

    def __repr__(self):
        return f"<Forecast city={self.city} +{self.horizon_hours}h={self.predicted_pm25}ug/m3 ({self.aqi_category})>"
