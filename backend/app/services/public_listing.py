from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.animal import Animal
from app.models.booking_request import BookingRequest
from app.models.listing import Listing
from app.models.listing_photo import ListingPhoto
from app.models.review import ModerationStatus, Review
from app.models.user import VerificationStatus
from app.schemas.public_listing import PublicListing
from app.services.storage import get_public_url


def _owner_last_initial(last_name: str) -> str:
    return last_name[:1].upper() if last_name else ""


def _photo_urls_for_listing(db: Session, listing: Listing) -> list[str]:
    photos = list(
        db.scalars(
            select(ListingPhoto)
            .where(
                ListingPhoto.listing_id == listing.id,
                ListingPhoto.moderation_status == ModerationStatus.APPROVED,
            )
            .order_by(ListingPhoto.is_primary.desc(), ListingPhoto.sort_order)
        ).all()
    )
    if photos:
        return [get_public_url(p.storage_key) for p in photos]
    return list(listing.animal.photo_urls or [])


def _review_aggregates(db: Session, listing_id) -> tuple[int, float | None]:
    row = db.execute(
        select(func.count(Review.id), func.avg(Review.rating))
        .select_from(Review)
        .join(BookingRequest, Review.booking_request_id == BookingRequest.id)
        .where(
            BookingRequest.listing_id == listing_id,
            Review.published_at.is_not(None),
            Review.moderation_status == ModerationStatus.APPROVED,
        )
    ).one()
    count = int(row[0] or 0)
    average = float(row[1]) if row[1] is not None else None
    return count, average


def listing_to_public(db: Session, listing: Listing) -> PublicListing:
    owner = listing.owner
    animal = listing.animal
    review_count, review_average = _review_aggregates(db, listing.id)
    member_since = owner.created_at.strftime("%B %Y")
    species_name = animal.species.name if getattr(animal, "species", None) else "horse"

    return PublicListing(
        animal_name=animal.name,
        species=species_name,
        breed=animal.breed,
        age=animal.age,
        photo_urls=_photo_urls_for_listing(db, listing),
        activity_type=listing.activity_type.value,
        price=listing.price if listing.price > 0 else None,
        display_location=listing.display_location,
        public_lat=listing.public_lat,
        public_lng=listing.public_lng,
        owner_first_name=owner.first_name,
        owner_last_initial=_owner_last_initial(owner.last_name),
        owner_verified=owner.verification_status == VerificationStatus.VERIFIED,
        owner_member_since=member_since,
        review_count=review_count,
        review_average=round(review_average, 1) if review_average is not None else None,
        slug=listing.slug,
        active=listing.active,
        riding_styles=list(animal.riding_styles or []),
    )


def get_listing_by_slug(db: Session, slug: str) -> Listing | None:
    return db.scalar(
        select(Listing)
        .options(
            selectinload(Listing.animal).selectinload(Animal.species),
            selectinload(Listing.owner),
        )
        .where(Listing.slug == slug)
    )
