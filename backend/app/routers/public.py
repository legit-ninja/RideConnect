from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.public_listing import PublicInvitePreview, PublicListing
from app.services.events import log_event
from app.services.public_listing import get_listing_by_slug, listing_to_public

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/listings/{slug}", response_model=PublicListing)
def get_public_listing(
    slug: str,
    db: Session = Depends(get_db),
    src: str | None = None,
) -> PublicListing:
    listing = get_listing_by_slug(db, slug)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    log_event(
        db,
        "public_listing_view",
        listing_slug=slug,
        src=src,
        payload={"active": listing.active},
    )
    db.commit()
    return listing_to_public(db, listing)
