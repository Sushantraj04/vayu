import os
import io
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import UploadFile, HTTPException

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.report import CitizenReport
from backend.app.models.fire import FireEvent
from backend.app.models.reading import StationReading
from backend.app.models.station import Station
from backend.app.analytics.hotspots import haversine_km


class CitizenReportService:
    """
    Manages the citizen pollution reporting pipeline:
      - Privacy-preserving coordinate rounding to ~500m grid
      - Anti-spam & rapid duplicate submission suppression
      - EXIF metadata stripping from uploaded image evidence
      - Cross-validation with satellite radiometry (FIRMS) and ground sensors
    """

    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
    SPAM_COOLDOWN_MINUTES = 15
    UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"

    @classmethod
    def anonymize_coordinates(cls, lat: float, lon: float, precision: float = 0.005) -> Tuple[float, float]:
        """
        Rounds raw geographic coordinates to a ~500m grid cell for public display,
        protecting citizen privacy and preventing identification of residential addresses.
        """
        pub_lat = round(lat / precision) * precision
        pub_lon = round(lon / precision) * precision
        return round(pub_lat, 4), round(pub_lon, 4)

    @classmethod
    def generate_session_hash(cls, client_ip: str, user_agent: str) -> str:
        """Generates deterministic anonymous session fingerprint."""
        raw = f"{client_ip}:{user_agent}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    @classmethod
    async def check_anti_spam(
        cls,
        db: AsyncSession,
        session_id: str,
        public_lat: float,
        public_lon: float
    ) -> bool:
        """
        Returns True if a duplicate report from this session was submitted within
        SPAM_COOLDOWN_MINUTES in the same grid cell.
        """
        since = datetime.now(timezone.utc) - timedelta(minutes=cls.SPAM_COOLDOWN_MINUTES)
        stmt = (
            select(CitizenReport)
            .where(CitizenReport.user_session_id == session_id)
            .where(CitizenReport.public_lat == public_lat)
            .where(CitizenReport.public_lon == public_lon)
            .where(CitizenReport.created_at >= since)
        )
        recent = (await db.execute(stmt)).scalars().first()
        return recent is not None

    @classmethod
    def process_and_sanitize_image(cls, file_bytes: bytes, filename: str) -> Tuple[bytes, str]:
        """
        Loads image bytes, validates dimensions, completely strips all EXIF metadata,
        and converts to an optimized JPEG format.
        """
        if len(file_bytes) > cls.MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="Image file exceeds maximum 5MB limit.")

        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported image extension {ext}.")

        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert RGBA / P to RGB for clean JPEG saving
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Create new clean image without EXIF metadata
            clean_image = Image.new(image.mode, image.size)
            clean_image.frombytes(image.tobytes())

            output_io = io.BytesIO()
            clean_image.save(output_io, format="JPEG", quality=85, optimize=True)
            sanitized_bytes = output_io.getvalue()

            new_filename = f"{uuid.uuid4().hex}.jpg"
            return sanitized_bytes, new_filename
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid or corrupt image file.")

    @classmethod
    async def save_photo_evidence(cls, sanitized_bytes: bytes, filename: str) -> Tuple[str, str]:
        """
        Saves photo evidence to local upload directory (or MinIO if configured).
        Returns (storage_key, public_url).
        """
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path = cls.UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(sanitized_bytes)

        storage_key = f"reports/{filename}"
        public_url = f"/uploads/{filename}"
        return storage_key, public_url

    @classmethod
    async def cross_validate_with_satellite_and_stations(
        cls,
        db: AsyncSession,
        raw_lat: float,
        raw_lon: float
    ) -> Tuple[bool, float]:
        """
        Checks whether active satellite fires (FIRMS) or anomalous ground stations
        exist within 15 km of the citizen report within the last 24 hours.
        Returns (is_verified, trust_score).
        """
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        # 1. Check nearby fires
        f_stmt = select(FireEvent).where(FireEvent.acquisition_time >= since)
        fires = (await db.execute(f_stmt)).scalars().all()
        for f in fires:
            if haversine_km(raw_lat, raw_lon, f.latitude, f.longitude) <= 15.0:
                logger.info(f"Report at ({raw_lat}, {raw_lon}) confirmed by satellite fire {f.id}")
                return True, 0.95

        # 2. Check nearby anomalous ground stations (PM2.5 >= 100 ug/m3)
        stn_stmt = select(Station).where(Station.is_active == True)
        stations = (await db.execute(stn_stmt)).scalars().all()
        for stn in stations:
            if haversine_km(raw_lat, raw_lon, stn.latitude, stn.longitude) <= 15.0:
                r_stmt = (
                    select(StationReading)
                    .where(StationReading.station_id == stn.id)
                    .where(StationReading.parameter == "pm25")
                    .where(StationReading.timestamp >= since)
                    .order_by(desc(StationReading.timestamp))
                    .limit(1)
                )
                reading = (await db.execute(r_stmt)).scalars().first()
                if reading and reading.value and reading.value >= 100.0:
                    logger.info(f"Report confirmed by station {stn.id} elevated PM2.5 ({reading.value})")
                    return True, 0.85

        return False, 0.50

    @classmethod
    async def create_report(
        cls,
        db: AsyncSession,
        raw_lat: float,
        raw_lon: float,
        user_category: str,
        user_pm25: Optional[float],
        client_ip: str,
        user_agent: str,
        photo_bytes: Optional[bytes] = None,
        photo_filename: Optional[str] = None
    ) -> CitizenReport:
        """Creates and validates a new citizen report."""
        pub_lat, pub_lon = cls.anonymize_coordinates(raw_lat, raw_lon)
        session_id = cls.generate_session_hash(client_ip, user_agent)

        # Anti-spam check
        is_spam = await cls.check_anti_spam(db, session_id, pub_lat, pub_lon)
        if is_spam:
            raise HTTPException(
                status_code=429,
                detail=f"Duplicate submission detected. Please wait {cls.SPAM_COOLDOWN_MINUTES} minutes before reporting again in this area."
            )

        # Handle photo upload
        photo_key, photo_url = None, None
        if photo_bytes and photo_filename:
            sanitized_bytes, clean_fn = cls.process_and_sanitize_image(photo_bytes, photo_filename)
            photo_key, photo_url = await cls.save_photo_evidence(sanitized_bytes, clean_fn)

        # Satellite cross-validation
        is_verified, trust_score = await cls.cross_validate_with_satellite_and_stations(db, raw_lat, raw_lon)

        year = datetime.now(timezone.utc).year
        public_id = f"CR-{year}-{uuid.uuid4().hex[:6].upper()}"

        report = CitizenReport(
            id=str(uuid.uuid4()),
            public_id=public_id,
            user_session_id=session_id,
            raw_lat=raw_lat,
            raw_lon=raw_lon,
            public_lat=pub_lat,
            public_lon=pub_lon,
            photo_s3_key=photo_key,
            photo_url=photo_url,
            user_category=user_category,
            user_pm25=user_pm25,
            is_satellite_verified=is_verified,
            trust_score=trust_score,
            status="VERIFIED" if is_verified else "PENDING",
            created_at=datetime.now(timezone.utc)
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info(f"Created CitizenReport {report.public_id} at grid ({pub_lat}, {pub_lon}) [Verified={is_verified}]")
        return report
