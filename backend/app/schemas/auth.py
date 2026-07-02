from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import VerificationStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    is_rider: bool = True
    is_owner: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_rider: bool
    is_owner: bool
    is_admin: bool
    verification_status: VerificationStatus
    is_minor: bool
    created_at: datetime

    model_config = {"from_attributes": True}
