from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.listing import ActivityType


class ListingCreateRequest(BaseModel):
    animal_id: UUID
    activity_type: ActivityType
    price: Decimal = Field(ge=0, decimal_places=2)
    availability: str | None = Field(default=None, max_length=2000)
    friend_only_allowed: bool = False
    active: bool = True
    display_location: str | None = Field(default=None, max_length=256)


class ListingUpdateRequest(BaseModel):
    activity_type: ActivityType | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    availability: str | None = Field(default=None, max_length=2000)
    friend_only_allowed: bool | None = None
    active: bool | None = None


class ListingSummary(BaseModel):
    id: UUID
    animal_id: UUID
    animal_name: str
    species_id: UUID
    activity_type: ActivityType
    price: Decimal
    availability: str | None
    friend_only_allowed: bool
    slug: str
    display_location: str
    public_lat: float
    public_lng: float
    photo_urls: list[str]
    created_at: datetime


class ListingDetail(ListingSummary):
    owner_id: UUID
    description: str | None
    breed: str | None
    active: bool


class ListingResponse(BaseModel):
    id: UUID
    animal_id: UUID
    owner_id: UUID
    activity_type: ActivityType
    price: Decimal
    availability: str | None
    friend_only_allowed: bool
    active: bool
    slug: str
    display_location: str
    public_lat: float
    public_lng: float
    created_at: datetime

    model_config = {"from_attributes": True}
