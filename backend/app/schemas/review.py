from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str | None = Field(default=None, max_length=2000)
    observed_rider_skill: int | None = Field(default=None, ge=1, le=5)


class ReviewResponse(BaseModel):
    id: UUID
    booking_request_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    rating: int
    body: str | None
    observed_rider_skill: int | None = None
    is_friend_ride: bool
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
