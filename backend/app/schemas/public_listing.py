from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, Field


class PublicListing(BaseModel):
    """Allowlist-only public listing response. No true location or contact fields."""

    animal_name: str
    species: str
    breed: str | None
    age: int | None
    photo_urls: list[str]
    activity_type: str
    price: Decimal | None
    display_location: str
    public_lat: float
    public_lng: float
    owner_first_name: str
    owner_last_initial: str
    owner_verified: bool
    owner_member_since: str
    review_count: int
    review_average: float | None
    slug: str
    active: bool


class PublicInvitePreview(BaseModel):
    owner_first_name: str
    owner_verified: bool
    animal_names: list[str]
    token_valid: bool
    expired: bool = False
    revoked: bool = False
