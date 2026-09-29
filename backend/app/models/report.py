import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Index
from backend.app.core.database import Base


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id = Column(String(20), unique=True, index=True, nullable=False) # e.g. CR-2026-8921
    user_session_id = Column(String(64), nullable=True, index=True) # Anonymous hashed session
    
    # Precise coordinate (Restricted administrative column)
    raw_lat = Column(Float, nullable=False)
    raw_lon = Column(Float, nullable=False)
    
    # Anonymized coordinate (~500m grid for public display)
    public_lat = Column(Float, nullable=False, index=True)
    public_lon = Column(Float, nullable=False, index=True)
    
    # Image storage
    photo_s3_key = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Citizen inputs
    user_category = Column(String(50), nullable=False) # smoke, open_burning, dust, industrial, other
    user_pm25 = Column(Float, nullable=True) # Optional low-cost sensor reading
    
    # Gemini AI Multimodal Vision classification
    gemini_classification = Column(String(50), nullable=True) # smoke, open_burning, dust, industrial, none, unclassified
    gemini_confidence = Column(Float, nullable=True)
    gemini_rationale = Column(String(500), nullable=True)
    
    # Satellite & Sensor Cross-Validation
    is_satellite_verified = Column(Boolean, default=False, nullable=False)
    trust_score = Column(Float, default=0.5, nullable=False) # 0.0 to 1.0
    
    # Moderation
    status = Column(String(30), default="PENDING", nullable=False, index=True) # PENDING, VERIFIED, REJECTED
    moderated_by = Column(String(36), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_report_public_coords", "public_lat", "public_lon"),
        Index("idx_report_status_created", "status", "created_at"),
    )

    def __repr__(self):
        return f"<CitizenReport {self.public_id} ({self.user_category}) Status={self.status}>"
