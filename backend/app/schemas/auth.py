from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import VerificationStatus


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


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_rider: bool
    is_owner: bool
    is_admin: bool
    verification_status: VerificationStatus
    is_minor: bool
    created_at: datetime
    # Computed from profile_photo_storage_key via get_public_url(); never a raw
    # storage key, and never derived from email/Gravatar. Null when the user has no
    # photo — clients should render initials as the default avatar, not Gravatar.
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
