from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import RiderType


class FamilyMemberResponse(BaseModel):
    id: UUID
    display_name: str
    rider_skill_level: int | None
    is_minor: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyMemberInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    rider_skill_level: int | None = Field(default=None, ge=1, le=5)
    is_minor: bool = False
    sort_order: int = Field(default=0, ge=0)


class UpdateFamilyProfileRequest(BaseModel):
    rider_type: RiderType
    family_name: str | None = Field(default=None, max_length=100)
    family_size: int | None = Field(default=None, ge=2, le=20)
    members: list[FamilyMemberInput] | None = None


class FamilyProfileResponse(BaseModel):
    rider_type: RiderType
    family_name: str | None
    family_size: int | None
    members: list[FamilyMemberResponse]
