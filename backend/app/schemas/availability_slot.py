from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.booking import BookingResponse


class CreateAvailabilitySlotRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    capacity: int = Field(default=1, ge=1, le=10)

    @model_validator(mode="after")
    def end_after_start(self) -> "CreateAvailabilitySlotRequest":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class UpdateAvailabilitySlotRequest(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: str | None = Field(default=None, pattern="^(open|blocked)$")

    @model_validator(mode="after")
    def validate_times(self) -> "UpdateAvailabilitySlotRequest":
        if self.start_at is not None and self.end_at is not None:
            if self.end_at <= self.start_at:
                raise ValueError("end_at must be after start_at")
        return self


class AvailabilitySlotResponse(BaseModel):
    id: UUID
    listing_id: UUID
    start_at: datetime
    end_at: datetime
    status: str
    capacity: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OpenSlotSummary(BaseModel):
    id: UUID
    listing_id: UUID
    slug: str
    animal_name: str
    activity_type: str
    price: Decimal
    display_location: str
    start_at: datetime
    end_at: datetime

    model_config = {"from_attributes": True}


class CalendarWeatherDay(BaseModel):
    date: str
    temp_max_f: float | None
    temp_min_f: float | None
    precip_probability_max: int | None
    wind_speed_max_mph: float | None
    weather_code: int | None
    ride_suitability: str
    summary: str


class CalendarDaySummary(BaseModel):
    date: str
    open_slot_count: int
    my_booking_count: int
    weather: CalendarWeatherDay | None = None


class CalendarResponse(BaseModel):
    days: list[CalendarDaySummary]
    open_slots: list[OpenSlotSummary]
    my_bookings: list[BookingResponse]
    weather_error: str | None = None
