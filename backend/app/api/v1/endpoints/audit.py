from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.core.security import RolePermissions
from backend.app.api.deps import require_role
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get("/", response_model=List[AuditLogOut])
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action code"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role([RolePermissions.ADMIN, RolePermissions.AUTHORITY, RolePermissions.ANALYST])),
    db: AsyncSession = Depends(get_db)
):
    """
    Query system audit trail for security, alerting actions, and administrative operations.
    Restricted to Authority, Analyst, and Admin roles.
    """
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()
