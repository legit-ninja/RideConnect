from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CreateFriendInviteRequest(BaseModel):
    invitee_email: EmailStr


class FriendInviteResponse(BaseModel):
    id: UUID
    owner_id: UUID
    rider_id: UUID | None
    invitee_email: EmailStr
    status: str
    invited_at: datetime
    accepted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendInviteListResponse(BaseModel):
    items: list[FriendInviteResponse]


class UpdateFriendInviteStatusRequest(BaseModel):
    status: str = Field(pattern="^(accepted|declined|cancelled)$")
