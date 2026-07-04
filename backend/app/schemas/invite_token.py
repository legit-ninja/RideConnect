from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateInviteTokenRequest(BaseModel):
    animal_id: UUID | None = None
    max_uses: int = Field(default=1, ge=1, le=10)
    expires_in_days: int = Field(default=14, ge=1, le=30)


class InviteTokenResponse(BaseModel):
    id: UUID
    token: str
    animal_id: UUID | None
    max_uses: int
    use_count: int
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    share_url: str

    model_config = {"from_attributes": True}


class InviteTokenListResponse(BaseModel):
    items: list[InviteTokenResponse]


class ConfirmInviteRequest(BaseModel):
    action: str = Field(pattern="^(confirm|decline)$")
