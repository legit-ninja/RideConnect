from decimal import Decimal

from app.models.animal import Animal
from app.models.listing import ActivityType, Listing
from app.models.user import VerificationStatus


def test_public_listings_only_active(
    client, db_session, horse_species
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="owner@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    animal = Animal(
        owner_id=owner.id,
        species_id=horse_species.id,
        name="Star",
        lat=36.2168,
        lng=-81.6746,
        address="Boone, NC",
        photo_urls=[],
    )
    db_session.add(animal)
    db_session.flush()
    active = Listing(
        animal_id=animal.id,
        owner_id=owner.id,
        activity_type=ActivityType.TRAIL_RIDE,
        price=Decimal("50.00"),
        active=True,
    )
    inactive = Listing(
        animal_id=animal.id,
        owner_id=owner.id,
        activity_type=ActivityType.LESSON,
        price=Decimal("40.00"),
        active=False,
    )
    db_session.add_all([active, inactive])
    db_session.commit()

    response = client.get("/listings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["animal_name"] == "Star"


def test_public_listings_filter_activity(
    client, db_session, horse_species
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="owner2@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    animal = Animal(
        owner_id=owner.id,
        species_id=horse_species.id,
        name="Daisy",
        lat=36.2168,
        lng=-81.6746,
        address="Boone, NC",
        photo_urls=[],
    )
    db_session.add(animal)
    db_session.flush()
    db_session.add_all(
        [
            Listing(
                animal_id=animal.id,
                owner_id=owner.id,
                activity_type=ActivityType.TRAIL_RIDE,
                price=Decimal("50.00"),
                active=True,
            ),
            Listing(
                animal_id=animal.id,
                owner_id=owner.id,
                activity_type=ActivityType.LESSON,
                price=Decimal("40.00"),
                active=True,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/listings?activity_type=lesson")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["activity_type"] == "lesson"
