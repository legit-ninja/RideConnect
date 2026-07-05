from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import RiderType, User, VerificationStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    is_rider: bool = True
    is_owner: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UpdateProfileRequest(BaseModel):
    is_horse_trainer: bool | None = None
    is_riding_instructor: bool | None = None
    rider_skill_level: int | None = Field(default=None, ge=1, le=5)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_rider: bool
    is_owner: bool
    is_horse_trainer: bool
    is_riding_instructor: bool
    trainer_verified: bool
    rider_skill_level: int | None
    rider_type: RiderType
    family_name: str | None
    family_size: int | None
    is_admin: bool
    verification_status: VerificationStatus
    is_minor: bool
    created_at: datetime
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
