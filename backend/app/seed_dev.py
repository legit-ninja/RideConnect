"""Dev-only seed data: users, animals, listings (Appalachian NC fixtures)."""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models.animal import Animal
from app.models.booking_request import BookingRequest, BookingStatus, PaymentType
from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.listing import ActivityType, Listing, TackProvided
from app.models.listing_availability_slot import ListingAvailabilitySlot, SlotStatus
from app.models.oauth_account import OAuthAccount, OAuthProvider
from app.models.review import ModerationStatus, Review
from app.models.rider_skill import RiderSkillLevel
from app.models.species import Species
from app.models.user import User, VerificationStatus
from app.services.flags import maybe_flag_trainer_minor_skew
from app.services.public_location import default_display_location, jitter_coordinates
from app.services.security import hash_password
from app.services.slug import generate_listing_slug

DEV_PASSWORD = "password123"

# Stable UUIDs for idempotent dev references
USER_IDS = {
    "owner_verified": uuid.UUID("11111111-1111-4111-8111-111111111101"),
    "owner_verified2": uuid.UUID("11111111-1111-4111-8111-111111111102"),
    "rider_verified": uuid.UUID("11111111-1111-4111-8111-111111111103"),
    "owner_pending": uuid.UUID("11111111-1111-4111-8111-111111111104"),
    "rider_unverified": uuid.UUID("11111111-1111-4111-8111-111111111105"),
    "rider_rejected": uuid.UUID("11111111-1111-4111-8111-111111111106"),
    "oauth_only": uuid.UUID("11111111-1111-4111-8111-111111111107"),
    "guardian": uuid.UUID("11111111-1111-4111-8111-111111111108"),
    "minor_rider": uuid.UUID("11111111-1111-4111-8111-111111111109"),
    "both_verified": uuid.UUID("11111111-1111-4111-8111-111111111110"),
    "minor_rider_2": uuid.UUID("11111111-1111-4111-8111-111111111111"),
    "minor_rider_3": uuid.UUID("11111111-1111-4111-8111-111111111112"),
    "minor_rider_4": uuid.UUID("11111111-1111-4111-8111-111111111113"),
}

PLACEHOLDER_PHOTO = "https://placehold.co/600x400/e8e8e8/666?text=RideConnect"

NC_LOCATIONS = [
    ("Boone, NC 28607", 36.2168, -81.6746),
    ("Asheville, NC 28801", 35.5951, -82.5515),
    ("Blowing Rock, NC 28605", 36.1351, -81.6720),
    ("Wilkesboro, NC 28697", 36.1450, -81.2668),
    ("Hickory, NC 28601", 35.7340, -81.3442),
]

HORSE_BREEDS = [
    "Quarter Horse",
    "Morgan",
    "Appaloosa",
    "Tennessee Walker",
    "Paint",
    "Arabian",
    "Thoroughbred",
    "Haflinger",
    "Mustang",
]

HORSE_NAMES = [
    "Buck",
    "Duke",
    "Clover",
    "Storm",
    "Honey",
    "Scout",
    "Blaze",
    "Pearl",
    "Ranger",
    "Sage",
    "Copper",
    "Luna",
    "Ace",
    "Ruby",
    "Finn",
    "Nova",
    "Oakley",
    "Piper",
    "Cash",
    "Ivy",
    "Colt",
    "Meadow",
    "Rocky",
    "Sierra",
    "Tucker",
    "Whisper",
    "Bandit",
    "Cinnamon",
    "Dusty",
    "Ember",
    "Fletcher",
    "Ginger",
    "Harley",
    "Jasper",
    "Koda",
]

BULK_ACTIVITY_TYPES = [
    ActivityType.TRAIL_RIDE,
    ActivityType.LESSON,
    ActivityType.LEASE,
    ActivityType.DAY_RENTAL,
]

_BULK_MIN_SKILLS: tuple[int | None, ...] = (None, 1, 3, 4)
_BULK_WEIGHTS: tuple[int | None, ...] = (None, 180, 200, 220)
_BULK_TACK = (TackProvided.PROVIDED, TackProvided.BRING_OWN, TackProvided.EITHER)


def _bulk_listing_community_fields(listing_idx: int) -> dict:
    return {
        "min_rider_skill": _BULK_MIN_SKILLS[listing_idx % len(_BULK_MIN_SKILLS)],
        "max_rider_weight_lbs": _BULK_WEIGHTS[listing_idx % len(_BULK_WEIGHTS)],
        "helmet_required": listing_idx % 7 != 0,
        "tack_provided": _BULK_TACK[listing_idx % len(_BULK_TACK)],
    }


def _allowed() -> bool:
    return settings.seed_dev_data or settings.environment == "development"


def _name_from_email(email: str) -> tuple[str, str]:
    local = email.split("@", 1)[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    if len(parts) >= 2:
        return parts[0].title(), parts[-1].title()
    return parts[0].title() if parts else "Member", ""


def upsert_user(
    db,
    *,
    user_id: uuid.UUID,
    email: str,
    is_rider: bool,
    is_owner: bool,
    verification_status: VerificationStatus,
    is_admin: bool = False,
    password_hash: str | None = None,
    is_minor: bool = False,
    guardian_user_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    is_horse_trainer: bool = False,
    is_riding_instructor: bool = False,
    trainer_verified: bool = False,
    rider_skill_level: int | None = None,
) -> User:
    derived_first, derived_last = _name_from_email(email)
    first_name = first_name or derived_first
    last_name = last_name or derived_last
    user = db.get(User, user_id)
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_rider=is_rider,
            is_owner=is_owner,
            is_admin=is_admin,
            verification_status=verification_status,
            is_minor=is_minor,
            guardian_user_id=guardian_user_id,
            is_horse_trainer=is_horse_trainer,
            is_riding_instructor=is_riding_instructor,
            trainer_verified=trainer_verified,
            rider_skill_level=rider_skill_level,
        )
        if created_at is not None:
            user.created_at = created_at
        db.add(user)
    else:
        user.email = email
        user.password_hash = password_hash
        user.first_name = first_name
        user.last_name = last_name
        user.is_rider = is_rider
        user.is_owner = is_owner
        user.is_admin = is_admin
        user.verification_status = verification_status
        user.is_minor = is_minor
        user.guardian_user_id = guardian_user_id
        user.is_horse_trainer = is_horse_trainer
        user.is_riding_instructor = is_riding_instructor
        user.trainer_verified = trainer_verified
        user.rider_skill_level = rider_skill_level
        if created_at is not None:
            user.created_at = created_at
    return user


def _bulk_user_id(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.user.bulk.{key}")


def _staggered_created_at(index: int, total: int) -> datetime:
    days_ago = max(0, 90 - (index * 90 // max(total, 1)))
    return datetime.now(UTC) - timedelta(days=days_ago)


def _rider_verification(index: int) -> VerificationStatus:
    if index % 5 < 3:
        return VerificationStatus.VERIFIED
    return [VerificationStatus.UNVERIFIED, VerificationStatus.PENDING, VerificationStatus.REJECTED][
        (index // 5) % 3
    ]


def _owner_verification(index: int) -> VerificationStatus:
    if index % 10 < 7:
        return VerificationStatus.VERIFIED
    return [VerificationStatus.UNVERIFIED, VerificationStatus.PENDING, VerificationStatus.REJECTED][
        index % 3
    ]


def _both_verification(index: int) -> VerificationStatus:
    if index % 5 < 4:
        return VerificationStatus.VERIFIED
    return VerificationStatus.PENDING if index % 2 == 0 else VerificationStatus.UNVERIFIED


def seed_bulk_users(db) -> dict[str, User]:
    hashed = hash_password(DEV_PASSWORD)
    bulk: dict[str, User] = {}
    slot = 0
    total = 50

    for n in range(1, 26):
        key = f"rider_{n:02d}"
        bulk[key] = upsert_user(
            db,
            user_id=_bulk_user_id(key),
            email=f"bulk.rider.{n:02d}@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=_rider_verification(n),
            password_hash=hashed,
            created_at=_staggered_created_at(slot, total),
            rider_skill_level=(n % 5) + 1 if n % 5 != 0 else None,
        )
        slot += 1

    for n in range(1, 16):
        key = f"owner_{n:02d}"
        is_trainer = n % 3 == 0
        bulk[key] = upsert_user(
            db,
            user_id=_bulk_user_id(key),
            email=f"bulk.owner.{n:02d}@example.com",
            is_rider=False,
            is_owner=True,
            verification_status=_owner_verification(n),
            password_hash=hashed,
            created_at=_staggered_created_at(slot, total),
            is_horse_trainer=is_trainer and n % 2 == 0,
            is_riding_instructor=is_trainer and n % 2 == 1,
        )
        slot += 1

    for n in range(1, 11):
        key = f"both_{n:02d}"
        is_trainer = n % 3 == 0
        bulk[key] = upsert_user(
            db,
            user_id=_bulk_user_id(key),
            email=f"bulk.both.{n:02d}@example.com",
            is_rider=True,
            is_owner=True,
            verification_status=_both_verification(n),
            password_hash=hashed,
            created_at=_staggered_created_at(slot, total),
            rider_skill_level=(n % 5) + 1 if n % 4 == 0 else None,
            is_horse_trainer=is_trainer and n % 2 == 0,
            is_riding_instructor=is_trainer and n % 2 == 1,
            trainer_verified=n in (2, 7),
        )
        slot += 1

    db.flush()
    return bulk


def seed_bulk_owner_assets(db, bulk: dict[str, User]) -> None:
    horse_id = get_species_id(db, "horse")
    name_idx = 0
    animals_created: list[tuple[str, Animal, User, bool]] = []

    def next_horse_name() -> str:
        nonlocal name_idx
        name = HORSE_NAMES[name_idx % len(HORSE_NAMES)]
        name_idx += 1
        return name

    def add_animal(owner_key: str, animal_suffix: str, owner: User) -> Animal:
        loc = NC_LOCATIONS[name_idx % len(NC_LOCATIONS)]
        address, lat, lng = loc
        key = f"{owner_key}-{animal_suffix}"
        animal = upsert_animal(
            db,
            key=key,
            owner=owner,
            species_id=horse_id,
            data={
                "name": next_horse_name(),
                "breed": HORSE_BREEDS[name_idx % len(HORSE_BREEDS)],
                "age": 5 + (name_idx % 12),
                "description": f"Registered dev horse for {owner.email}.",
                "lat": lat,
                "lng": lng,
                "address": address,
                "photo_urls": [PLACEHOLDER_PHOTO],
            },
        )
        return animal

    for n in range(1, 9):
        owner = bulk[f"owner_{n:02d}"]
        animal = add_animal(f"owner-{n:02d}", "horse-1", owner)
        with_listing = n > 2
        animals_created.append((f"owner-{n:02d}-horse-1", animal, owner, with_listing))

    for n in range(9, 16):
        owner = bulk[f"owner_{n:02d}"]
        for suffix in ("horse-1", "horse-2"):
            animal = add_animal(f"owner-{n:02d}", suffix, owner)
            with_listing = not (n == 9 and suffix == "horse-2")
            animals_created.append((f"owner-{n:02d}-{suffix}", animal, owner, with_listing))

    for n in range(1, 6):
        owner = bulk[f"both_{n:02d}"]
        if owner.verification_status != VerificationStatus.VERIFIED:
            continue
        animal = add_animal(f"both-{n:02d}", "horse-1", owner)
        animals_created.append((f"both-{n:02d}-horse-1", animal, owner, True))

    listing_idx = 0
    for animal_key, animal, owner, with_listing in animals_created:
        if not with_listing:
            continue
        activity = BULK_ACTIVITY_TYPES[listing_idx % len(BULK_ACTIVITY_TYPES)]
        price = Decimal(str(35 + (listing_idx % 9) * 10))
        inactive = listing_idx == 3
        upsert_listing(
            db,
            key=f"bulk-{animal_key}",
            owner=owner,
            animal=animal,
            data={
                "activity_type": activity,
                "price": price,
                "availability": "Weekends by appointment",
                "friend_only_allowed": False,
                "active": not inactive,
                **_bulk_listing_community_fields(listing_idx),
            },
        )
        listing_idx += 1


def seed_users(db) -> dict[str, User]:
    hashed = hash_password(DEV_PASSWORD)
    users = {
        "owner_verified": upsert_user(
            db,
            user_id=USER_IDS["owner_verified"],
            email="owner.verified@example.com",
            is_rider=False,
            is_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_riding_instructor=True,
        ),
        "owner_verified2": upsert_user(
            db,
            user_id=USER_IDS["owner_verified2"],
            email="owner.verified2@example.com",
            is_rider=False,
            is_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_horse_trainer=True,
            is_riding_instructor=True,
            trainer_verified=True,
        ),
        "rider_verified": upsert_user(
            db,
            user_id=USER_IDS["rider_verified"],
            email="rider.verified@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            rider_skill_level=RiderSkillLevel.BEGINNER.value,
        ),
        "owner_pending": upsert_user(
            db,
            user_id=USER_IDS["owner_pending"],
            email="owner.pending@example.com",
            is_rider=False,
            is_owner=True,
            verification_status=VerificationStatus.PENDING,
            password_hash=hashed,
        ),
        "rider_unverified": upsert_user(
            db,
            user_id=USER_IDS["rider_unverified"],
            email="rider.unverified@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.UNVERIFIED,
            password_hash=hashed,
        ),
        "rider_rejected": upsert_user(
            db,
            user_id=USER_IDS["rider_rejected"],
            email="rider.rejected@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.REJECTED,
            password_hash=hashed,
        ),
        "guardian": upsert_user(
            db,
            user_id=USER_IDS["guardian"],
            email="guardian@example.com",
            is_rider=True,
            is_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
        ),
        "minor_rider": upsert_user(
            db,
            user_id=USER_IDS["minor_rider"],
            email="minor.rider@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.UNVERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
        ),
        "oauth_only": upsert_user(
            db,
            user_id=USER_IDS["oauth_only"],
            email="oauth.only@example.com",
            is_rider=False,
            is_owner=False,
            verification_status=VerificationStatus.UNVERIFIED,
            password_hash=None,
        ),
        "both_verified": upsert_user(
            db,
            user_id=USER_IDS["both_verified"],
            email="both.verified@example.com",
            is_rider=True,
            is_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            rider_skill_level=RiderSkillLevel.INTERMEDIATE.value,
        ),
        "minor_rider_2": upsert_user(
            db,
            user_id=USER_IDS["minor_rider_2"],
            email="minor.rider2@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
            first_name="Casey",
            last_name="Minor",
        ),
        "minor_rider_3": upsert_user(
            db,
            user_id=USER_IDS["minor_rider_3"],
            email="minor.rider3@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
            first_name="Jordan",
            last_name="Minor",
        ),
        "minor_rider_4": upsert_user(
            db,
            user_id=USER_IDS["minor_rider_4"],
            email="minor.rider4@example.com",
            is_rider=True,
            is_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
            first_name="Taylor",
            last_name="Minor",
        ),
    }
    db.flush()

    oauth_user = users["oauth_only"]
    oauth = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == OAuthProvider.GOOGLE,
            OAuthAccount.provider_user_id == "google-dev-oauth-only",
        )
    )
    if oauth is None:
        db.add(
            OAuthAccount(
                user_id=oauth_user.id,
                provider=OAuthProvider.GOOGLE,
                provider_user_id="google-dev-oauth-only",
                provider_email=oauth_user.email,
                provider_email_verified=True,
            )
        )
    return users


def get_species_id(db, name: str) -> uuid.UUID:
    species = db.scalar(select(Species).where(Species.name == name))
    if species is None:
        raise RuntimeError(f"Species '{name}' not found — run migrations first")
    return species.id


def upsert_animal(db, *, key: str, owner: User, species_id: uuid.UUID, data: dict) -> Animal:
    animal_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.animal.{key}")
    animal = db.get(Animal, animal_id)
    if animal is None:
        animal = Animal(id=animal_id, owner_id=owner.id, species_id=species_id, **data)
        db.add(animal)
    else:
        for field, value in data.items():
            setattr(animal, field, value)
        animal.owner_id = owner.id
        animal.species_id = species_id
    return animal


def upsert_listing(db, *, key: str, owner: User, animal: Animal, data: dict) -> Listing:
    listing_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.listing.{key}")
    listing = db.get(Listing, listing_id)
    display_location = data.pop("display_location", None) or default_display_location(animal.address)
    if listing is None:
        slug = generate_listing_slug(animal.name)
        public_lat, public_lng = jitter_coordinates(
            animal.id, animal.lat, animal.lng, settings.location_jitter_secret
        )
        listing = Listing(
            id=listing_id,
            animal_id=animal.id,
            owner_id=owner.id,
            slug=slug,
            display_location=display_location,
            public_lat=public_lat,
            public_lng=public_lng,
            **data,
        )
        db.add(listing)
    else:
        listing.animal_id = animal.id
        listing.owner_id = owner.id
        if not listing.slug:
            listing.slug = generate_listing_slug(animal.name)
        if listing.public_lat is None or listing.public_lng is None:
            listing.public_lat, listing.public_lng = jitter_coordinates(
                animal.id, animal.lat, animal.lng, settings.location_jitter_secret
            )
        listing.display_location = display_location
        for field, value in data.items():
            setattr(listing, field, value)
    return listing


def seed_animals_and_listings(db, users: dict[str, User]) -> None:
    horse_id = get_species_id(db, "horse")
    owner1 = users["owner_verified"]
    owner2 = users["owner_verified2"]

    animals_data = [
        (
            "star",
            owner1,
            {
                "name": "Star",
                "breed": "Quarter Horse",
                "age": 8,
                "description": "Calm trail horse, great for beginners on mountain paths.",
                "lat": 36.2168,
                "lng": -81.6746,
                "address": "742 Mountain Rd, Boone, NC 28607",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["western"],
            },
        ),
        (
            "misty",
            owner1,
            {
                "name": "Misty",
                "breed": "Tennessee Walker",
                "age": 12,
                "description": "Smooth-gaited mare for scenic Blue Ridge rides.",
                "lat": 35.5951,
                "lng": -82.5515,
                "address": "Asheville, NC 28801",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["english"],
            },
        ),
        (
            "rusty",
            owner1,
            {
                "name": "Rusty",
                "breed": "Paint",
                "age": 6,
                "description": "Energetic gelding suited for intermediate riders.",
                "lat": 36.1351,
                "lng": -81.6720,
                "address": "Blowing Rock, NC 28605",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["western", "english"],
            },
        ),
        (
            "daisy",
            owner2,
            {
                "name": "Daisy",
                "breed": "Appaloosa",
                "age": 10,
                "description": "Lesson horse with years of arena experience.",
                "lat": 36.2185,
                "lng": -81.6812,
                "address": "Boone, NC 28607",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["english"],
            },
        ),
        (
            "comet",
            owner2,
            {
                "name": "Comet",
                "breed": "Arabian",
                "age": 7,
                "description": "Day rental available for experienced riders.",
                "lat": 35.6009,
                "lng": -82.5540,
                "address": "88 Riverside Dr, Asheville, NC 28801",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["western"],
            },
        ),
        (
            "willow",
            owner2,
            {
                "name": "Willow",
                "breed": "Morgan",
                "age": 9,
                "description": "Gentle lesson horse for children and adults.",
                "lat": 36.1450,
                "lng": -81.2668,
                "address": "Wilkesboro, NC 28697",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["therapy"],
            },
        ),
        (
            "shadow",
            owner2,
            {
                "name": "Shadow",
                "breed": "Thoroughbred",
                "age": 5,
                "description": "Athletic gelding for lease arrangements.",
                "lat": 35.7340,
                "lng": -81.3442,
                "address": "Hickory, NC 28601",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["english"],
            },
        ),
        (
            "maple",
            users["both_verified"],
            {
                "name": "Maple",
                "breed": "Haflinger",
                "age": 11,
                "description": "Family-friendly trail horse on a small ranch.",
                "lat": 36.2100,
                "lng": -81.6800,
                "address": "Boone, NC 28607",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["western", "english"],
            },
        ),
        (
            "river",
            users["both_verified"],
            {
                "name": "River",
                "breed": "Mustang",
                "age": 8,
                "description": "Trail rides along the New River corridor.",
                "lat": 36.1400,
                "lng": -81.6700,
                "address": "Blowing Rock, NC 28605",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "riding_styles": ["western"],
            },
        ),
    ]

    animals: dict[str, Animal] = {}
    for key, owner, data in animals_data:
        animals[key] = upsert_animal(db, key=key, owner=owner, species_id=horse_id, data=data)

    listings_data = [
        (
            "star-trail",
            animals["star"],
            owner1,
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("75.00"),
                "availability": "Saturday and Sunday mornings",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "misty-trail",
            animals["misty"],
            owner1,
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("85.00"),
                "availability": "Weekends by appointment",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "rusty-lesson",
            animals["rusty"],
            owner1,
            {
                "activity_type": ActivityType.LESSON,
                "price": Decimal("60.00"),
                "availability": "Tuesday and Thursday afternoons",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "daisy-lesson",
            animals["daisy"],
            owner2,
            {
                "activity_type": ActivityType.LESSON,
                "price": Decimal("55.00"),
                "availability": "Weekday mornings",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "comet-rental",
            animals["comet"],
            owner2,
            {
                "activity_type": ActivityType.DAY_RENTAL,
                "price": Decimal("120.00"),
                "availability": "Advance booking required",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "star-friend",
            animals["star"],
            owner1,
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("0.00"),
                "availability": "Verified friends only — contact via platform",
                "friend_only_allowed": True,
                "active": True,
            },
        ),
        (
            "misty-inactive",
            animals["misty"],
            owner1,
            {
                "activity_type": ActivityType.LEASE,
                "price": Decimal("300.00"),
                "availability": "Monthly lease — currently paused",
                "friend_only_allowed": False,
                "active": False,
            },
        ),
        (
            "willow-lesson",
            animals["willow"],
            owner2,
            {
                "activity_type": ActivityType.LESSON,
                "price": Decimal("45.00"),
                "availability": "After-school slots",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "shadow-lease",
            animals["shadow"],
            owner2,
            {
                "activity_type": ActivityType.LEASE,
                "price": Decimal("150.00"),
                "availability": "Monthly partial lease",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "daisy-trail",
            animals["daisy"],
            owner2,
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("65.00"),
                "availability": "Weekend mornings",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "comet-day",
            animals["comet"],
            owner2,
            {
                "activity_type": ActivityType.DAY_RENTAL,
                "price": Decimal("110.00"),
                "availability": "Full day, rider supplies tack",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "rusty-friend",
            animals["rusty"],
            owner1,
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("0.00"),
                "availability": "Verified friends only",
                "friend_only_allowed": True,
                "active": True,
            },
        ),
        (
            "maple-trail",
            animals["maple"],
            users["both_verified"],
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("55.00"),
                "availability": "Saturday afternoons",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "maple-lesson",
            animals["maple"],
            users["both_verified"],
            {
                "activity_type": ActivityType.LESSON,
                "price": Decimal("40.00"),
                "availability": "Weekday evenings",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "river-trail",
            animals["river"],
            users["both_verified"],
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("70.00"),
                "availability": "Sunday group rides",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "river-friend",
            animals["river"],
            users["both_verified"],
            {
                "activity_type": ActivityType.TRAIL_RIDE,
                "price": Decimal("0.00"),
                "availability": "Friends and family only",
                "friend_only_allowed": True,
                "active": True,
            },
        ),
        (
            "star-lesson",
            animals["star"],
            owner1,
            {
                "activity_type": ActivityType.LESSON,
                "price": Decimal("50.00"),
                "availability": "Beginner lessons — weekday mornings",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
        (
            "misty-lease",
            animals["misty"],
            owner1,
            {
                "activity_type": ActivityType.LEASE,
                "price": Decimal("250.00"),
                "availability": "Monthly lease — 3 rides per week",
                "friend_only_allowed": False,
                "active": True,
            },
        ),
    ]

    _CURATED_LISTING_COMMUNITY: dict[str, dict] = {
        "star-trail": {
            "min_rider_skill": RiderSkillLevel.BEGINNER.value,
            "helmet_required": True,
            "tack_provided": TackProvided.PROVIDED,
        },
        "star-lesson": {
            "min_rider_skill": RiderSkillLevel.BEGINNER.value,
            "max_rider_weight_lbs": 200,
            "helmet_required": True,
            "tack_provided": TackProvided.PROVIDED,
        },
        "willow-lesson": {
            "min_rider_skill": RiderSkillLevel.BEGINNER.value,
            "max_rider_weight_lbs": 220,
            "helmet_required": True,
            "tack_provided": TackProvided.PROVIDED,
        },
        "rusty-lesson": {
            "min_rider_skill": RiderSkillLevel.INTERMEDIATE.value,
            "helmet_required": True,
            "tack_provided": TackProvided.EITHER,
        },
        "daisy-lesson": {
            "min_rider_skill": RiderSkillLevel.INTERMEDIATE.value,
            "helmet_required": True,
            "tack_provided": TackProvided.EITHER,
        },
        "comet-rental": {
            "min_rider_skill": RiderSkillLevel.ADVANCED_INTERMEDIATE.value,
            "max_rider_weight_lbs": 180,
            "helmet_required": True,
            "tack_provided": TackProvided.BRING_OWN,
        },
        "shadow-lease": {
            "min_rider_skill": RiderSkillLevel.ADVANCED_INTERMEDIATE.value,
            "max_rider_weight_lbs": 175,
            "helmet_required": True,
            "tack_provided": TackProvided.BRING_OWN,
        },
        "star-friend": {"min_rider_skill": RiderSkillLevel.BEGINNER.value},
        "rusty-friend": {"min_rider_skill": RiderSkillLevel.BEGINNER.value},
        "river-friend": {"min_rider_skill": RiderSkillLevel.BEGINNER.value},
    }

    for key, animal, owner, data in listings_data:
        merged = {**data, **_CURATED_LISTING_COMMUNITY.get(key, {})}
        upsert_listing(db, key=key, owner=owner, animal=animal, data=merged)


def upsert_availability_slot(
    db,
    *,
    key: str,
    listing: Listing,
    start_at: datetime,
    end_at: datetime,
    status: SlotStatus = SlotStatus.OPEN,
) -> ListingAvailabilitySlot:
    slot_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.slot.{key}")
    slot = db.get(ListingAvailabilitySlot, slot_id)
    if slot is None:
        slot = ListingAvailabilitySlot(
            id=slot_id,
            listing_id=listing.id,
            start_at=start_at,
            end_at=end_at,
            status=status,
        )
        db.add(slot)
    else:
        slot.listing_id = listing.id
        slot.start_at = start_at
        slot.end_at = end_at
        slot.status = status
    return slot


def seed_availability_slots(db) -> None:
    """Open slots on a few active listings for calendar discovery in dev."""
    listing_keys = ("star-trail", "misty-trail", "rusty-lesson")
    base = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    for listing_index, listing_key in enumerate(listing_keys):
        listing_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.listing.{listing_key}")
        listing = db.get(Listing, listing_id)
        if listing is None or not listing.active:
            continue
        for day_offset in (2, 5, 9, 13):
            start_at = base + timedelta(days=day_offset, hours=10 + listing_index)
            end_at = start_at + timedelta(hours=2)
            upsert_availability_slot(
                db,
                key=f"{listing_key}-d{day_offset}",
                listing=listing,
                start_at=start_at,
                end_at=end_at,
            )


def upsert_friend_invite(
    db,
    *,
    key: str,
    owner: User,
    rider: User | None,
    email: str,
    status: FriendInviteStatus,
    created_at: datetime | None = None,
) -> FriendInvite:
    invite_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.friend.{key}")
    invite = db.get(FriendInvite, invite_id)
    if invite is None:
        invite = FriendInvite(
            id=invite_id,
            owner_id=owner.id,
            rider_id=rider.id if rider else None,
            invitee_email=email.lower(),
            status=status,
        )
        if created_at is not None:
            invite.created_at = created_at
            invite.invited_at = created_at
        db.add(invite)
    else:
        invite.owner_id = owner.id
        invite.rider_id = rider.id if rider else None
        invite.invitee_email = email.lower()
        invite.status = status
        if created_at is not None:
            invite.created_at = created_at
            invite.invited_at = created_at
    return invite


def seed_friend_invites(db, users: dict[str, User], bulk: dict[str, User]) -> None:
    owner = users["owner_verified"]
    trainer_owner = users["owner_verified2"]
    rider = users["rider_verified"]
    recent = datetime.now(UTC) - timedelta(days=14)

    upsert_friend_invite(
        db,
        key="owner-rider-accepted",
        owner=owner,
        rider=rider,
        email=rider.email,
        status=FriendInviteStatus.ACTIVE,
    )
    upsert_friend_invite(
        db,
        key="owner-unverified-pending",
        owner=owner,
        rider=users["rider_unverified"],
        email=users["rider_unverified"].email,
        status=FriendInviteStatus.PENDING_OWNER_CONFIRM,
    )

    for idx, minor_key in enumerate(("minor_rider_2", "minor_rider_3", "minor_rider_4"), start=1):
        minor = users[minor_key]
        upsert_friend_invite(
            db,
            key=f"trainer-minor-{idx}",
            owner=trainer_owner,
            rider=minor,
            email=minor.email,
            status=FriendInviteStatus.ACTIVE,
            created_at=recent - timedelta(days=idx),
        )

    for idx, bulk_key in enumerate(("rider_01", "rider_02"), start=1):
        adult = bulk[bulk_key]
        upsert_friend_invite(
            db,
            key=f"trainer-adult-{idx}",
            owner=trainer_owner,
            rider=adult,
            email=adult.email,
            status=FriendInviteStatus.ACTIVE,
            created_at=recent - timedelta(days=idx + 3),
        )

    maybe_flag_trainer_minor_skew(db, trainer_owner.id)


def upsert_booking(db, *, key: str, listing: Listing, rider: User, status: BookingStatus, payment_type: PaymentType, note: str | None = None) -> BookingRequest:
    booking_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.booking.{key}")
    booking = db.get(BookingRequest, booking_id)
    if booking is None:
        booking = BookingRequest(
            id=booking_id,
            listing_id=listing.id,
            rider_id=rider.id,
            owner_id=listing.owner_id,
            payment_type=payment_type,
            status=status,
            note=note,
        )
        db.add(booking)
    else:
        booking.listing_id = listing.id
        booking.rider_id = rider.id
        booking.owner_id = listing.owner_id
        booking.payment_type = payment_type
        booking.status = status
        booking.note = note
    return booking


def seed_booking_requests(db, users: dict[str, User]) -> None:
    star_trail_id = uuid.uuid5(uuid.NAMESPACE_DNS, "rideconnect.dev.listing.star-trail")
    rusty_lesson_id = uuid.uuid5(uuid.NAMESPACE_DNS, "rideconnect.dev.listing.rusty-lesson")
    comet_rental_id = uuid.uuid5(uuid.NAMESPACE_DNS, "rideconnect.dev.listing.comet-rental")
    daisy_trail_id = uuid.uuid5(uuid.NAMESPACE_DNS, "rideconnect.dev.listing.daisy-trail")
    star_trail = db.get(Listing, star_trail_id)
    rusty_lesson = db.get(Listing, rusty_lesson_id)
    comet_rental = db.get(Listing, comet_rental_id)
    daisy_trail = db.get(Listing, daisy_trail_id)
    if star_trail is None or rusty_lesson is None:
        return
    rider = users["rider_verified"]
    upsert_booking(
        db,
        key="pending-paid",
        listing=star_trail,
        rider=rider,
        status=BookingStatus.PENDING_PAYMENT,
        payment_type=PaymentType.PAID,
        note="Hope to ride Saturday morning",
    )
    upsert_booking(
        db,
        key="approved-paid",
        listing=rusty_lesson,
        rider=rider,
        status=BookingStatus.APPROVED,
        payment_type=PaymentType.PAID,
    )
    upsert_booking(
        db,
        key="declined-paid",
        listing=star_trail,
        rider=users["both_verified"],
        status=BookingStatus.DECLINED,
        payment_type=PaymentType.PAID,
        note="Schedule conflict",
    )
    if comet_rental is not None:
        upsert_booking(
            db,
            key="skill-mismatch-pending",
            listing=comet_rental,
            rider=rider,
            status=BookingStatus.PENDING_OWNER,
            payment_type=PaymentType.PAID,
            note="Interested in a full-day rental",
        )
    if daisy_trail is not None:
        upsert_booking(
            db,
            key="completed-daisy-trail",
            listing=daisy_trail,
            rider=users["both_verified"],
            status=BookingStatus.COMPLETED,
            payment_type=PaymentType.PAID,
        )
        upsert_booking(
            db,
            key="completed-rusty-lesson",
            listing=rusty_lesson,
            rider=users["both_verified"],
            status=BookingStatus.COMPLETED,
            payment_type=PaymentType.PAID,
        )


def upsert_review(
    db,
    *,
    key: str,
    booking: BookingRequest,
    reviewer: User,
    reviewee: User,
    rating: int,
    observed_rider_skill: int | None = None,
    body: str | None = None,
    published_at: datetime | None = None,
) -> Review:
    review_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"rideconnect.dev.review.{key}")
    review = db.get(Review, review_id)
    if review is None:
        review = Review(
            id=review_id,
            booking_request_id=booking.id,
            reviewer_id=reviewer.id,
            reviewee_id=reviewee.id,
            rating=rating,
            body=body,
            observed_rider_skill=observed_rider_skill,
            moderation_status=ModerationStatus.APPROVED,
            published_at=published_at or datetime.now(UTC),
        )
        db.add(review)
    else:
        review.booking_request_id = booking.id
        review.reviewer_id = reviewer.id
        review.reviewee_id = reviewee.id
        review.rating = rating
        review.body = body
        review.observed_rider_skill = observed_rider_skill
        review.moderation_status = ModerationStatus.APPROVED
        review.published_at = published_at or datetime.now(UTC)
    return review


def seed_reviews(db, users: dict[str, User]) -> None:
    daisy_booking_id = uuid.uuid5(uuid.NAMESPACE_DNS, "rideconnect.dev.booking.completed-daisy-trail")
    rusty_booking_id = uuid.uuid5(uuid.NAMESPACE_DNS, "rideconnect.dev.booking.completed-rusty-lesson")
    daisy_booking = db.get(BookingRequest, daisy_booking_id)
    rusty_booking = db.get(BookingRequest, rusty_booking_id)
    if daisy_booking is None or rusty_booking is None:
        return
    rider = users["both_verified"]
    published = datetime.now(UTC) - timedelta(days=7)
    upsert_review(
        db,
        key="owner2-observed-both",
        booking=daisy_booking,
        reviewer=users["owner_verified2"],
        reviewee=rider,
        rating=5,
        observed_rider_skill=RiderSkillLevel.INTERMEDIATE.value,
        body="Solid intermediate rider on the trail.",
        published_at=published,
    )
    upsert_review(
        db,
        key="owner1-observed-both",
        booking=rusty_booking,
        reviewer=users["owner_verified"],
        reviewee=rider,
        rating=4,
        observed_rider_skill=RiderSkillLevel.INTERMEDIATE.value,
        body="Handled the lesson horse confidently.",
        published_at=published,
    )


def run_seed() -> None:
    if not _allowed():
        print("Refusing to seed: set SEED_DEV_DATA=true or ENVIRONMENT=development")
        sys.exit(1)

    db = SessionLocal()
    try:
        users = seed_users(db)
        bulk = seed_bulk_users(db)
        seed_animals_and_listings(db, users)
        seed_availability_slots(db)
        seed_bulk_owner_assets(db, bulk)
        seed_friend_invites(db, users, bulk)
        seed_booking_requests(db, users)
        seed_reviews(db, users)
        db.commit()
        print("Dev seed complete.")
        print(f"Dev password for email users: {DEV_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
