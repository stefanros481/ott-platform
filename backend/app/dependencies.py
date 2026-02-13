import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import Profile, User

security = HTTPBearer()

DB = Annotated[AsyncSession, Depends(get_db)]


def decode_token(token: str) -> dict:
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DB,
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_verified_profile_id(
    user: CurrentUser,
    db: DB,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
) -> uuid.UUID:
    result = await db.execute(
        select(Profile.id).where(
            and_(Profile.id == profile_id, Profile.user_id == user.id)
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile not found or access denied",
        )
    return profile_id


VerifiedProfileId = Annotated[uuid.UUID, Depends(get_verified_profile_id)]


async def get_optional_verified_profile_id(
    user: CurrentUser,
    db: DB,
    profile_id: uuid.UUID | None = Query(None, description="Active profile"),
) -> uuid.UUID | None:
    if profile_id is None:
        return None
    result = await db.execute(
        select(Profile.id).where(
            and_(Profile.id == profile_id, Profile.user_id == user.id)
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile not found or access denied",
        )
    return profile_id


OptionalVerifiedProfileId = Annotated[uuid.UUID | None, Depends(get_optional_verified_profile_id)]


async def get_admin_user(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


AdminUser = Annotated[User, Depends(get_admin_user)]
