from decimal import Decimal

from app.models.listing import ActivityType
from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing


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
    seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="Star",
        activity_type=ActivityType.TRAIL_RIDE,
        price=Decimal("50.00"),
        active=True,
    )
    seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="Star2",
        activity_type=ActivityType.LESSON,
        price=Decimal("40.00"),
        active=False,
    )

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
    seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="Daisy",
        activity_type=ActivityType.TRAIL_RIDE,
        price=Decimal("50.00"),
        active=True,
    )
    seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="Daisy2",
        activity_type=ActivityType.LESSON,
        price=Decimal("40.00"),
        active=True,
    )

    response = client.get("/listings?activity_type=lesson")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["activity_type"] == "lesson"
