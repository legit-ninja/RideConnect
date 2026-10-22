from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.shop import BusinessUnit


class FunnelEventCreate(BaseModel):
    business_unit: BusinessUnit
    stage: str = Field(min_length=1, max_length=64)
    anon_id: str | None = Field(default=None, max_length=64)
    src: str | None = Field(default=None, max_length=64)
    ref: str | None = Field(default=None, max_length=128)
    path: str | None = Field(default=None, max_length=512)
    payload: dict[str, Any] | None = None


class FunnelEventResponse(BaseModel):
    id: UUID
    ok: bool = True
