from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import decode_token, oauth2_scheme, api_key_header, RolePermissions
from backend.app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    """
    Authenticates user via either JWT Bearer token, Partner API Key header, or development role header.
    """
    # 1. Check Partner API Key
    if api_key:
        stmt = select(User).where(User.api_key == api_key, User.is_active == True)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked Partner API Key",
        )

    # Check raw Authorization header if oauth2_scheme didn't capture it
    if not token:
        raw_auth = request.headers.get("authorization")
        if raw_auth and raw_auth.lower().startswith("bearer "):
            token = raw_auth.split(" ", 1)[1].strip()

    # 2. Check Bearer Token
    if token:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type (expected access token)",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token subject invalid",
            )

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token not found",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        return user

    # 3. Development / Demo role header fallback
    role_hdr = request.headers.get("x-user-role")
    if role_hdr and settings.ENVIRONMENT == "development":
        stmt_role = select(User).where(User.role == role_hdr, User.is_active == True)
        user_by_role = (await db.execute(stmt_role)).scalars().first()
        if user_by_role:
            return user_by_role

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials not provided",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[User]:
    """Allows anonymous public access while attaching user if authenticated."""
    try:
        return await get_current_user(request=request, db=db, token=token, api_key=api_key)
    except HTTPException:
        return None


def require_role(allowed_roles: List[str]):
    """Enforces role-based access control (RBAC)."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != RolePermissions.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {allowed_roles}. Current role: {current_user.role}",
            )
        return current_user
    return role_checker
