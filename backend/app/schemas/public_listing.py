from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.listing import TackProvided


def tack_provided_label(value: TackProvided | str) -> str:
    if isinstance(value, str):
        value = TackProvided(value)
    labels = {
        TackProvided.PROVIDED: "Tack provided",
        TackProvided.BRING_OWN: "Bring your own tack",
        TackProvided.EITHER: "Tack provided or bring your own",
    }
    return labels[value]


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
    owner_trainer_verified: bool = False
    owner_member_since: str
    review_count: int
    review_average: float | None
    slug: str
    active: bool
    riding_styles: list[str] = Field(default_factory=list)
    min_rider_skill: int | None = None
    min_rider_skill_label: str | None = None
    max_rider_weight_lbs: int | None = None
    helmet_required: bool = True
    tack_provided: str = TackProvided.EITHER.value
    tack_provided_label: str = tack_provided_label(TackProvided.EITHER)


class PublicInvitePreview(BaseModel):
    owner_first_name: str
    owner_verified: bool
    animal_names: list[str]
    token_valid: bool
    expired: bool = False
    revoked: bool = False
