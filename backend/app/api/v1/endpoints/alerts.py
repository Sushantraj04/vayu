from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.database import get_db
from backend.app.core.security import RolePermissions
from backend.app.api.deps import require_role, get_current_user
from backend.app.models.user import User
from backend.app.models.alert import Alert
from backend.app.models.audit import AuditLog
from backend.app.models.station import Station
from backend.app.models.forecast import Forecast
from backend.app.models.hotspot import Hotspot
from backend.app.models.report import CitizenReport

from backend.app.analytics.alert_rules import AlertRuleEngine
from backend.app.notifications.dispatcher import CAPFormatter, NotificationDispatcher

router = APIRouter()


@router.get("/")
async def list_alerts(
    corridor_id: Optional[str] = Query(None, description="Filter by corridor ID"),
    severity: Optional[str] = Query(None, description="MODERATE, HIGH, SEVERE, CRITICAL"),
    status: Optional[str] = Query(None, description="NEW, ACKNOWLEDGED, RESOLVED"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Returns alerts across corridor airsheds."""
    stmt = select(Alert)
    if corridor_id:
        stmt = stmt.where(Alert.corridor_id == corridor_id)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if status:
        stmt = stmt.where(Alert.status == status)
    stmt = stmt.order_by(desc(Alert.created_at)).limit(limit)

    alerts = (await db.execute(stmt)).scalars().all()
    return alerts


@router.get("/cap/{cap_identifier}")
async def export_cap_xml(
    cap_identifier: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Exports a specific alert in standard OASIS Common Alerting Protocol (CAP v1.2) XML.
    Compatible with National Disaster Management Authority (NDMA) feeds.
    """
    stmt = select(Alert).where(Alert.cap_identifier == cap_identifier)
    alert = (await db.execute(stmt)).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    xml_content = CAPFormatter.to_cap_xml(alert)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/feed.atom")
async def export_cap_atom_feed(
    db: AsyncSession = Depends(get_db)
):
    """
    Exports public syndication CAP 1.2 Atom feed for sirens, broadcast, and emergency agencies.
    """
    stmt = select(Alert).order_by(desc(Alert.created_at)).limit(50)
    alerts = (await db.execute(stmt)).scalars().all()

    feed_xml = CAPFormatter.to_atom_feed(alerts)
    return Response(content=feed_xml, media_type="application/atom+xml")


@router.post("/evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_alert_rules(
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates automated environmental rules:
      1. Sustained High AQI (PM2.5 >= 250 ug/m3)
      2. Predictive Forecast Spikes (24h spike >= 200 ug/m3)
      3. Trans-boundary Smoke Inflow
      4. Ground Citizen Report Clusters
    Enforces cooldown rate-limiting and dispatches notifications.
    """
    rule_engine = AlertRuleEngine()
    created_alerts: List[Alert] = []

    # 1. Evaluate Sustained High AQI
    stn_stmt = select(Station).where(Station.is_active == True)
    stations = (await db.execute(stn_stmt)).scalars().all()
    aqi_alerts = await rule_engine.evaluate_sustained_high_aqi(db, stations)
    created_alerts.extend(aqi_alerts)

    # 2. Evaluate Forecast Spikes
    fc_stmt = select(Forecast).where(Forecast.horizon_hours == 24).order_by(desc(Forecast.created_at)).limit(20)
    forecasts = (await db.execute(fc_stmt)).scalars().all()
    fc_alerts = await rule_engine.evaluate_forecast_spikes(db, forecasts)
    created_alerts.extend(fc_alerts)

    # 3. Evaluate Trans-Boundary Inflow
    h_stmt = select(Hotspot).where(Hotspot.is_active == True)
    hotspots = (await db.execute(h_stmt)).scalars().all()
    target_cities = [
        ("Delhi-NCR", 28.6139, 77.2090),
        ("Ambala", 30.3782, 76.7767),
        ("Agra", 27.1767, 78.0081),
        ("Kanpur", 26.4499, 80.3319)
    ]
    trans_alerts = await rule_engine.evaluate_trans_boundary_plumes(db, hotspots, target_cities)
    created_alerts.extend(trans_alerts)

    # 4. Evaluate Citizen Report Clusters
    rep_stmt = select(CitizenReport).order_by(desc(CitizenReport.created_at)).limit(50)
    reports = (await db.execute(rep_stmt)).scalars().all()
    rep_alerts = await rule_engine.evaluate_citizen_report_clusters(db, reports)
    created_alerts.extend(rep_alerts)

    # Persist and dispatch
    for a in created_alerts:
        db.add(a)
        await NotificationDispatcher.dispatch_alert(a)

    await db.commit()

    return {
        "message": f"Rule evaluation complete. {len(created_alerts)} new alerts generated.",
        "count": len(created_alerts),
        "alerts": [
            {
                "id": a.id,
                "city": a.city,
                "severity": a.severity,
                "rule_trigger": a.rule_trigger,
                "cap_identifier": a.cap_identifier,
                "title_en": a.title_en,
            }
            for a in created_alerts
        ]
    }


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(require_role([RolePermissions.AUTHORITY, RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Authority operation to acknowledge an emergency alert."""
    stmt = select(Alert).where(Alert.id == alert_id)
    alert = (await db.execute(stmt)).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_by_email = current_user.email
    alert.acknowledged_at = datetime.now(timezone.utc)

    # Log to audit trail
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        action="ALERT_ACKNOWLEDGED",
        resource_type="alert",
        resource_id=alert.id,
        details={"city": alert.city, "severity": alert.severity}
    )
    db.add(audit)
    await db.commit()
    return {"status": "success", "alert_status": alert.status}


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_role([RolePermissions.AUTHORITY, RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Authority operation to resolve an active alert."""
    stmt = select(Alert).where(Alert.id == alert_id)
    alert = (await db.execute(stmt)).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.resolved_by = current_user.id
    alert.resolved_by_email = current_user.email
    alert.resolved_at = datetime.now(timezone.utc)

    # Log to audit trail
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        action="ALERT_RESOLVED",
        resource_type="alert",
        resource_id=alert.id,
        details={"city": alert.city, "severity": alert.severity}
    )
    db.add(audit)
    await db.commit()
    return {"status": "success", "alert_status": alert.status}
