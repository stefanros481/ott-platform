"""Pydantic schemas for authentication and user profile endpoints."""

import uuid

from pydantic import BaseModel, Field, field_validator

_EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def _validate_email(v: str) -> str:
    import re

    if not re.match(_EMAIL_PATTERN, v):
        raise ValueError("Invalid email address")
    return v.lower().strip()


# ── Request schemas ──────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    avatar_url: str | None = None
    parental_rating: str = "TV-MA"
    is_kids: bool = False


# ── Response schemas ─────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    subscription_tier: str
    is_admin: bool

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    avatar_url: str | None = None
    parental_rating: str
    is_kids: bool

    model_config = {"from_attributes": True}
