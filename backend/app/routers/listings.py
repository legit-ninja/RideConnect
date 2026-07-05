from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import require_rider, require_verified
from app.models.listing import ActivityType
from app.models.riding_style import RidingStyle
from app.models.user import User
from app.schemas.availability_slot import AvailabilitySlotResponse
from app.schemas.listing import ListingDetail, ListingSummary
from app.services.calendar import get_open_slots_for_listing
from app.services.listings import (
    get_listing_detail,
    listing_to_detail,
    listing_to_summary,
    search_listings,
)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=list[ListingSummary])
def list_public_listings(
    db: Session = Depends(get_db),
    activity_type: ActivityType | None = None,
    species_id: UUID | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    riding_style: RidingStyle | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = Query(default=None, gt=0),
) -> list[ListingSummary]:
    # Authz: public read of active listings only; no auth required.
    listings = search_listings(
        db,
        activity_type=activity_type,
        species_id=species_id,
        min_price=min_price,
        max_price=max_price,
        riding_style=riding_style,
        lat=lat if lat is not None else settings.search_default_lat,
        lng=lng if lng is not None else settings.search_default_lng,
        radius_km=radius_km if radius_km is not None else settings.search_default_radius_km,
        active_only=True,
    )
    return [listing_to_summary(listing) for listing in listings]


@router.get("/{listing_id}", response_model=ListingDetail)
def get_listing_detail_authenticated(
    listing_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_verified),
) -> ListingDetail:
    # Authz: verified users may read full listing detail including description.
    listing = get_listing_detail(db, listing_id)
    if listing is None or not listing.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing_to_detail(listing)


@router.get("/{listing_id}/slots", response_model=list[AvailabilitySlotResponse])
def list_listing_open_slots(
    listing_id: UUID,
    db: Session = Depends(get_db),
    _rider: User = Depends(require_rider),
) -> list[AvailabilitySlotResponse]:
    # Authz: verified riders may view bookable open slots on active listings.
    listing = get_listing_detail(db, listing_id)
    if listing is None or not listing.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    slots = get_open_slots_for_listing(db, listing_id)
    return [AvailabilitySlotResponse.model_validate(slot) for slot in slots]
