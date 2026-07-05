from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateBookingRequest(BaseModel):
    listing_id: UUID
    availability_slot_id: UUID | None = None
    note: str | None = Field(default=None, max_length=2000)
    family_member_ids: list[UUID] | None = None


class BookingParticipantResponse(BaseModel):
    booking_id: UUID
    family_member_id: UUID | None
    participant_display_name: str | None
    rider_skill_warning: str | None = None


class UpdateBookingStatusRequest(BaseModel):
    status: str = Field(pattern="^(approved|declined|cancelled|completed)$")


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
    availability_slot_id: UUID | None = None
    note: str | None
    requested_at: datetime
    listing_price: Decimal
    activity_type: str
    thread_id: UUID | None = None
    rider_skill_warning: str | None = None
    family_booking_group_id: UUID | None = None
    family_member_id: UUID | None = None
    participant_display_name: str | None = None
    is_family_booking: bool = False
    family_party_size: int | None = None
    booker_family_name: str | None = None
    family_participants: list[BookingParticipantResponse] | None = None

    model_config = {"from_attributes": True}


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
