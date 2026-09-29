import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import get_password_hash, RolePermissions
from backend.app.api.deps import require_role, get_current_user
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.user import UserOut, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role([RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """List all registered system users (Admin only)."""
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    request: Request,
    current_user: User = Depends(require_role([RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new operator, analyst, or authority user (Admin only)."""
    stmt = select(User).where(User.email == user_in.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active,
    )
    if user_in.role == RolePermissions.PARTNER_API_KEY:
        new_user.api_key = f"vayu_live_{secrets.token_urlsafe(32)}"

    db.add(new_user)
    await db.flush()

    # Log audit event
    audit_entry = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        action="USER_CREATED",
        resource_type="user",
        resource_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role},
        ip_address=request.client.host if request.client else None
    )
    db.add(audit_entry)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/generate-api-key")
async def generate_partner_api_key(
    request: Request,
    partner_name: str,
    current_user: User = Depends(require_role([RolePermissions.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Generates an operational API key for BRICS partner cities/institutions."""
    api_key_str = f"vayu_partner_{secrets.token_urlsafe(32)}"
    partner_email = f"partner-{secrets.token_hex(4)}@partner.vayu-net.org"

    partner_user = User(
        email=partner_email,
        hashed_password=get_password_hash(secrets.token_urlsafe(16)),
        full_name=f"Partner API - {partner_name}",
        role=RolePermissions.PARTNER_API_KEY,
        api_key=api_key_str,
        is_active=True
    )
    db.add(partner_user)
    await db.flush()

    audit_entry = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        action="PARTNER_KEY_GENERATED",
        resource_type="partner_key",
        resource_id=partner_user.id,
        details={"partner_name": partner_name, "key_prefix": api_key_str[:12]},
        ip_address=request.client.host if request.client else None
    )
    db.add(audit_entry)
    await db.commit()

    return {
        "partner_name": partner_name,
        "api_key": api_key_str,
        "role": RolePermissions.PARTNER_API_KEY,
        "notice": "Store this key securely. It will not be shown again in full plaintext."
    }
