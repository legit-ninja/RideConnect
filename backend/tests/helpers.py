from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.animal import Animal
from app.models.listing import ActivityType, Listing
from app.models.user import User
from app.services.public_location import default_display_location, jitter_coordinates
from app.services.slug import generate_listing_slug


def seed_test_listing(
    db: Session,
    *,
    horse_species,
    owner: User,
    animal_name: str = "TestHorse",
    activity_type: ActivityType = ActivityType.TRAIL_RIDE,
    price: Decimal = Decimal("50.00"),
    friend_only_allowed: bool = False,
    active: bool = True,
    lat: float = 36.2,
    lng: float = -81.6,
    address: str = "Boone, NC",
) -> Listing:
    animal = Animal(
        owner_id=owner.id,
        species_id=horse_species.id,
        name=animal_name,
        lat=lat,
        lng=lng,
        address=address,
        photo_urls=[],
    )
    db.add(animal)
    db.flush()
    public_lat, public_lng = jitter_coordinates(lat, lng)
    listing = Listing(
        animal_id=animal.id,
        owner_id=owner.id,
        activity_type=activity_type,
        price=price,
        friend_only_allowed=friend_only_allowed,
        active=active,
        slug=generate_listing_slug(animal_name),
        display_location=default_display_location(address),
        public_lat=public_lat,
        public_lng=public_lng,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing
