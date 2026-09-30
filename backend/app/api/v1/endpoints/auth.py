from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    RolePermissions
)
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.token import Token, LoginRequest, RefreshTokenRequest
from backend.app.schemas.user import UserOut

router = APIRouter()


@router.post("/role-token", response_model=Token)
async def get_role_token(
    role: str = Query("admin", description="Role to get access token for (admin, authority, analyst, partner-api-key)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a valid cryptographic JWT access token for a given role (used by frontend role switcher).
    """
    role_email_map = {
        "admin": "admin@vayu-net.org",
        "authority": "authority@vayu-net.org",
        "analyst": "analyst@vayu-net.org",
        "partner-api-key": "partner@brics-climate.org",
        "public": "admin@vayu-net.org"
    }
    target_email = role_email_map.get(role, "admin@vayu-net.org")
    stmt = select(User).where(User.email == target_email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        stmt2 = select(User).where(User.role == role, User.is_active == True)
        user = (await db.execute(stmt2)).scalars().first()

    if not user:
        # Fallback to first active user
        stmt3 = select(User).where(User.is_active == True)
        user = (await db.execute(stmt3)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail=f"No user found for role '{role}'")

    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id, role=user.role)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )



@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user via email and password, returning JWT access and refresh tokens.
    """
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated",
        )

    access_token = create_access_token(subject=user.id, role=user.role)
    refresh_token = create_refresh_token(subject=user.id, role=user.role)

    # Record login audit event
    client_ip = request.client.host if request.client else "unknown"
    audit_entry = AuditLog(
        user_id=user.id,
        user_email=user.email,
        user_role=user.role,
        action="USER_LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=user.id,
        details={"email": user.email, "role": user.role},
        ip_address=client_ip
    )
    db.add(audit_entry)
    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refreshes an expired access token using a valid refresh token.
    """
    payload = decode_token(refresh_data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type (expected refresh token)"
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or no longer exists"
        )

    access_token = create_access_token(subject=user.id, role=user.role)
    new_refresh_token = create_refresh_token(subject=user.id, role=user.role)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        role=user.role,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the authenticated user profile and assigned role.
    """
    return current_user
