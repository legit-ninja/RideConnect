from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing


def test_trainer_without_owner_cannot_manage_slots(client, db_session, horse_species) -> None:
    from datetime import UTC, datetime, timedelta

    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-slots@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    trainer = create_user(
        db_session,
        email="trainer-slots@example.com",
        is_riding_instructor=True,
        is_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)

    start = datetime.now(UTC) + timedelta(days=3)
    end = start + timedelta(hours=2)
    create_resp = client.post(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(trainer),
        json={"start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert create_resp.status_code == 403


def test_trainer_without_owner_cannot_create_listing(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-animals@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    trainer = create_user(
        db_session,
        email="trainer-listing@example.com",
        is_horse_trainer=True,
        is_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    from app.models.animal import Animal

    animal = Animal(
        owner_id=owner.id,
        species_id=horse_species.id,
        name="NotMine",
        lat=36.2,
        lng=-81.6,
        address="Boone, NC",
    )
    db_session.add(animal)
    db_session.commit()

    response = client.post(
        "/owner/listings",
        headers=auth_header(trainer),
        json={
            "animal_id": str(animal.id),
            "activity_type": "trail_ride",
            "price": "50.00",
        },
    )
    assert response.status_code == 403


def test_trainer_without_owner_cannot_view_owner_bookings(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    trainer = create_user(
        db_session,
        email="trainer-bookings@example.com",
        is_riding_instructor=True,
        is_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.get(
        "/bookings",
        params={"role": "owner"},
        headers=auth_header(trainer),
    )
    assert response.status_code == 403
