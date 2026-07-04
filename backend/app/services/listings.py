import math
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.animal import Animal
from app.models.listing import ActivityType, Listing
from app.models.species import Species
from app.schemas.listing import ListingDetail, ListingSummary


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def listing_to_summary(listing: Listing) -> ListingSummary:
    animal = listing.animal
    return ListingSummary(
        id=listing.id,
        animal_id=listing.animal_id,
        animal_name=animal.name,
        species_id=animal.species_id,
        activity_type=listing.activity_type,
        price=listing.price,
        availability=listing.availability,
        friend_only_allowed=listing.friend_only_allowed,
        slug=listing.slug,
        display_location=listing.display_location,
        public_lat=listing.public_lat,
        public_lng=listing.public_lng,
        photo_urls=list(animal.photo_urls or []),
        created_at=listing.created_at,
    )


def listing_to_detail(listing: Listing) -> ListingDetail:
    summary = listing_to_summary(listing)
    animal = listing.animal
    return ListingDetail(
        **summary.model_dump(),
        owner_id=listing.owner_id,
        description=animal.description,
        breed=animal.breed,
        active=listing.active,
    )


def search_listings(
    db: Session,
    *,
    activity_type: ActivityType | None,
    species_id: UUID | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
    lat: float,
    lng: float,
    radius_km: float,
    active_only: bool = True,
    owner_id: UUID | None = None,
) -> list[Listing]:
    stmt = select(Listing).options(
        selectinload(Listing.animal).selectinload(Animal.species)
    )
    if active_only:
        stmt = stmt.where(Listing.active.is_(True))
    if owner_id is not None:
        stmt = stmt.where(Listing.owner_id == owner_id)
    if activity_type is not None:
        stmt = stmt.where(Listing.activity_type == activity_type)
    if min_price is not None:
        stmt = stmt.where(Listing.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Listing.price <= max_price)
    if species_id is not None:
        stmt = stmt.join(Animal, Listing.animal_id == Animal.id).where(
            Animal.species_id == species_id
        )

    listings = list(db.scalars(stmt.order_by(Listing.created_at.desc())).all())

    filtered: list[Listing] = []
    for listing in listings:
        distance = haversine_km(lat, lng, listing.public_lat, listing.public_lng)
        if distance <= radius_km:
            filtered.append(listing)
    return filtered


def get_listing_detail(db: Session, listing_id: UUID) -> Listing | None:
    return db.scalar(
        select(Listing)
        .options(selectinload(Listing.animal).selectinload(Animal.species))
        .where(Listing.id == listing_id)
    )


def get_species_by_id(db: Session, species_id: UUID) -> Species | None:
    return db.get(Species, species_id)
