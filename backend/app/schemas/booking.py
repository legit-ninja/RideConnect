from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateBookingRequest(BaseModel):
    listing_id: UUID
    scheduled_at: datetime | None = None
    note: str | None = Field(default=None, max_length=2000)


class UpdateBookingStatusRequest(BaseModel):
    status: str = Field(pattern="^(approved|declined|cancelled)$")


class BookingResponse(BaseModel):
    id: UUID
    listing_id: UUID
    animal_name: str
    rider_id: UUID
    rider_email: str
    rider_verification_status: str
    owner_id: UUID
    owner_email: str
    payment_type: str
    status: str
    scheduled_at: datetime | None
    note: str | None
    requested_at: datetime
    listing_price: Decimal
    activity_type: str

    model_config = {"from_attributes": True}


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
