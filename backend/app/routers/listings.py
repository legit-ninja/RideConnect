from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.listing import ActivityType
from app.schemas.listing import ListingDetail, ListingSummary
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
        lat=lat if lat is not None else settings.search_default_lat,
        lng=lng if lng is not None else settings.search_default_lng,
        radius_km=radius_km if radius_km is not None else settings.search_default_radius_km,
        active_only=True,
    )
    return [listing_to_summary(listing) for listing in listings]


@router.get("/{listing_id}", response_model=ListingDetail)
def get_public_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
) -> ListingDetail:
    # Authz: public read of a single active listing.
    listing = get_listing_detail(db, listing_id)
    if listing is None or not listing.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing_to_detail(listing)
