from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.security import RolePermissions
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.models.report import CitizenReport
from backend.app.services.citizen_reports import CitizenReportService

router = APIRouter()


class CitizenReportJSONPayload(BaseModel):
    latitude: float
    longitude: float
    category: str
    user_pm25: Optional[float] = None
    consent: bool = True


class ModerateReportPayload(BaseModel):
    status: str # VERIFIED, REJECTED
    rationale: Optional[str] = None


@router.get("/")
async def list_public_reports(
    status: Optional[str] = Query(None, description="Filter reports (VERIFIED, PENDING, REJECTED)"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Public citizen incident reports feed.
    Privacy by Design: Coordinates are rounded to ~500m grid for public display.
    No personally identifiable information (PII) is exposed.
    """
    stmt = select(CitizenReport)
    if status:
        stmt = stmt.where(CitizenReport.status == status)
    stmt = stmt.order_by(desc(CitizenReport.created_at)).limit(limit)
    reports = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": r.id,
            "public_id": r.public_id,
            "public_lat": r.public_lat,
            "public_lon": r.public_lon,
            "user_category": r.user_category,
            "user_pm25": r.user_pm25,
            "is_satellite_verified": r.is_satellite_verified,
            "trust_score": r.trust_score,
            "status": r.status,
            "photo_url": r.photo_url,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_citizen_report(
    request: Request,
    latitude: float = Form(..., description="Latitude coordinate from device GPS"),
    longitude: float = Form(..., description="Longitude coordinate from device GPS"),
    category: str = Form(..., description="smoke, open_burning, dust, industrial, other"),
    user_pm25: Optional[float] = Form(None, description="Optional local sensor reading (ug/m3)"),
    consent: bool = Form(True, description="Consent for public mapping"),
    photo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Citizen pollution report submission.
    Applies privacy-by-design EXIF sanitization and 500m coordinate rounding.
    Cross-validates with satellite fires (FIRMS) and ground sensors.
    """
    if not consent:
        raise HTTPException(status_code=400, detail="Consent for public mapping is mandatory.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    photo_bytes = None
    photo_filename = None
    if photo and photo.filename:
        photo_bytes = await photo.read()
        photo_filename = photo.filename

    report = await CitizenReportService.create_report(
        db=db,
        raw_lat=latitude,
        raw_lon=longitude,
        user_category=category,
        user_pm25=user_pm25,
        client_ip=client_ip,
        user_agent=user_agent,
        photo_bytes=photo_bytes,
        photo_filename=photo_filename
    )

    return {
        "status": "success",
        "public_id": report.public_id,
        "public_lat": report.public_lat,
        "public_lon": report.public_lon,
        "is_satellite_verified": report.is_satellite_verified,
        "trust_score": report.trust_score,
        "message": "Report received. EXIF stripped, coordinates rounded to 500m grid for privacy."
    }


@router.post("/json", status_code=status.HTTP_201_CREATED)
async def submit_citizen_report_json(
    request: Request,
    payload: CitizenReportJSONPayload,
    db: AsyncSession = Depends(get_db)
):
    """JSON API submission endpoint for citizen reports."""
    if not payload.consent:
        raise HTTPException(status_code=400, detail="Consent for public mapping is mandatory.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    report = await CitizenReportService.create_report(
        db=db,
        raw_lat=payload.latitude,
        raw_lon=payload.longitude,
        user_category=payload.category,
        user_pm25=payload.user_pm25,
        client_ip=client_ip,
        user_agent=user_agent
    )

    return {
        "status": "success",
        "public_id": report.public_id,
        "public_lat": report.public_lat,
        "public_lon": report.public_lon,
        "is_satellite_verified": report.is_satellite_verified,
        "trust_score": report.trust_score,
        "message": "Report received. EXIF stripped, coordinates rounded to 500m grid for privacy."
    }


@router.get("/queue")
async def get_moderation_queue(
    current_user: User = Depends(require_role([RolePermissions.AUTHORITY, RolePermissions.ANALYST, RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Authority and Analyst moderation queue for reviewing and triaging incident reports."""
    stmt = select(CitizenReport).order_by(desc(CitizenReport.created_at)).limit(100)
    reports = (await db.execute(stmt)).scalars().all()
    return reports


@router.patch("/{report_id}/moderate")
async def moderate_report(
    report_id: str,
    payload: ModerateReportPayload,
    current_user: User = Depends(require_role([RolePermissions.AUTHORITY, RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Authority operation to verify or reject a citizen report."""
    if payload.status not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Status must be VERIFIED or REJECTED.")

    stmt = select(CitizenReport).where(CitizenReport.id == report_id)
    report = (await db.execute(stmt)).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = payload.status
    report.moderated_by = current_user.id
    report.moderated_at = datetime.now(timezone.utc)
    if payload.rationale:
        report.gemini_rationale = payload.rationale

    await db.commit()
    return {
        "status": "success",
        "report_id": report.id,
        "public_id": report.public_id,
        "new_status": report.status
    }
