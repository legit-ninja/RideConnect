from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.listing import ActivityType, TackProvided


class ListingCreateRequest(BaseModel):
    animal_id: UUID
    activity_type: ActivityType
    price: Decimal = Field(ge=0, decimal_places=2)
    availability: str | None = Field(default=None, max_length=2000)
    friend_only_allowed: bool = False
    active: bool = True
    display_location: str | None = Field(default=None, max_length=256)
    min_rider_skill: int | None = Field(default=None, ge=1, le=5)
    max_rider_weight_lbs: int | None = Field(default=None, ge=50, le=500)
    helmet_required: bool = True
    tack_provided: TackProvided = TackProvided.EITHER


class ListingUpdateRequest(BaseModel):
    activity_type: ActivityType | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    availability: str | None = Field(default=None, max_length=2000)
    friend_only_allowed: bool | None = None
    active: bool | None = None
    min_rider_skill: int | None = Field(default=None, ge=1, le=5)
    max_rider_weight_lbs: int | None = Field(default=None, ge=50, le=500)
    helmet_required: bool | None = None
    tack_provided: TackProvided | None = None


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
    riding_styles: list[str] = Field(default_factory=list)
    min_rider_skill: int | None = None
    max_rider_weight_lbs: int | None = None
    helmet_required: bool = True
    tack_provided: TackProvided = TackProvided.EITHER
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
    min_rider_skill: int | None = None
    max_rider_weight_lbs: int | None = None
    helmet_required: bool = True
    tack_provided: TackProvided = TackProvided.EITHER
    created_at: datetime

    model_config = {"from_attributes": True}
