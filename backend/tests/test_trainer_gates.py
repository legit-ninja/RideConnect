from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing, seed_test_slot


def test_trainer_can_manage_listing_slots(client, db_session, horse_species) -> None:
    from datetime import UTC, datetime, timedelta

    from tests.conftest import auth_header, create_user

    trainer = create_user(
        db_session,
        email="trainer-slots@example.com",
        is_trainer=True,
        is_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=trainer)

    start = datetime.now(UTC) + timedelta(days=3)
    end = start + timedelta(hours=2)
    create_resp = client.post(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(trainer),
        json={"start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert create_resp.status_code == 201

    list_resp = client.get(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(trainer),
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_non_host_cannot_manage_slots(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-gate@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-gate@example.com",
        is_rider=True,
        is_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)

    response = client.get(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(rider),
    )
    assert response.status_code == 403


def test_trainer_can_view_host_booking_inbox(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    trainer = create_user(
        db_session,
        email="trainer-inbox@example.com",
        is_trainer=True,
        is_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-inbox@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=trainer)
    slot = seed_test_slot(db_session, listing=listing)

    client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id), "availability_slot_id": str(slot.id)},
    )

    inbox = client.get("/bookings?role=owner", headers=auth_header(trainer))
    assert inbox.status_code == 200
    assert inbox.json()["total"] == 1
