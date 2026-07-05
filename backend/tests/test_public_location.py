import math
from uuid import UUID

import pytest

from app.services.public_location import (
    default_display_location,
    deterministic_jitter,
    jitter_coordinates,
)


TEST_SECRET = "test-jitter-secret"
ANIMAL_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("123 Hidden Farm Rd, Boone, NC 28607", "Boone"),
        ("Boone, NC 28607", "Boone"),
        ("123 Hidden Farm Rd, 28607", "Appalachian NC"),
        ("456 Oak Ln, Boone", "Appalachian NC"),
        ("PO Box 12, Asheville, NC", "Asheville"),
        (None, "Appalachian NC"),
        ("SingleToken", "Appalachian NC"),
    ],
)
def test_default_display_location(address: str | None, expected: str) -> None:
    assert default_display_location(address) == expected


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def test_deterministic_jitter_is_stable() -> None:
    lat, lng = 36.2, -81.6
    a = deterministic_jitter(ANIMAL_ID, lat, lng, TEST_SECRET)
    b = deterministic_jitter(ANIMAL_ID, lat, lng, TEST_SECRET)
    assert a == b


def test_deterministic_jitter_within_distance_band() -> None:
    lat, lng = 36.2, -81.6
    pub_lat, pub_lng = deterministic_jitter(ANIMAL_ID, lat, lng, TEST_SECRET)
    dist = _haversine_km(lat, lng, pub_lat, pub_lng)
    assert 5.0 <= dist <= 8.0 + 0.01


def test_jitter_alias_matches_deterministic() -> None:
    lat, lng = 36.2, -81.6
    assert jitter_coordinates(ANIMAL_ID, lat, lng, TEST_SECRET) == deterministic_jitter(
        ANIMAL_ID, lat, lng, TEST_SECRET
    )


def test_same_animal_listings_share_identical_public_coordinates(
    db_session, horse_species
) -> None:
    from decimal import Decimal

    from app.models.animal import Animal
    from app.models.listing import Listing
    from app.services.public_location import default_display_location
    from app.services.slug import generate_listing_slug
    from tests.conftest import create_user

    owner = create_user(db_session, email="jitter-owner@test.com", is_owner=True)
    animal = Animal(
        owner_id=owner.id,
        species_id=horse_species.id,
        name="SharedJitter",
        lat=36.21,
        lng=-81.67,
        address="Boone, NC",
    )
    db_session.add(animal)
    db_session.flush()

    coords: list[tuple[float, float]] = []
    for i in range(3):
        pub_lat, pub_lng = jitter_coordinates(animal.id, animal.lat, animal.lng, TEST_SECRET)
        listing = Listing(
            animal_id=animal.id,
            owner_id=owner.id,
            activity_type="trail_ride",
            price=Decimal("40.00"),
            slug=generate_listing_slug(f"SharedJitter-{i}"),
            display_location=default_display_location(animal.address),
            public_lat=pub_lat,
            public_lng=pub_lng,
        )
        db_session.add(listing)
        coords.append((pub_lat, pub_lng))
    db_session.commit()

    assert coords[0] == coords[1] == coords[2]
