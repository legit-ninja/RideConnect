from decimal import Decimal

from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing


def test_unverified_rider_cannot_book(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-bk@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-bk-unv@example.com",
        is_rider=True,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    response = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id)},
    )
    assert response.status_code == 403


def test_verified_rider_creates_paid_booking(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-bk2@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-bk2@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    response = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id), "note": "Saturday morning"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["payment_type"] == "paid"
    assert data["status"] == "pending_payment"


def test_owner_approves_booking(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-bk3@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-bk3@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    create_resp = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id)},
    )
    booking_id = create_resp.json()["id"]
    response = client.patch(
        f"/bookings/{booking_id}",
        headers=auth_header(owner),
        json={"status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_free_booking_requires_friend_invite(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-bk4@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-bk4@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        animal_name="FriendHorse",
        price=Decimal("0.00"),
        friend_only_allowed=True,
    )

    response = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id)},
    )
    assert response.status_code == 403

    invite = FriendInvite(
        owner_id=owner.id,
        rider_id=rider.id,
        invitee_email=rider.email,
        status=FriendInviteStatus.ACTIVE,
    )
    db_session.add(invite)
    db_session.commit()

    response2 = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id)},
    )
    assert response2.status_code == 201
    assert response2.json()["payment_type"] == "free"


def test_booking_with_slot_is_held_then_released_on_decline(
    client, db_session, horse_species
) -> None:
    from tests.conftest import auth_header, create_user

    from app.models.listing_availability_slot import SlotStatus
    from tests.helpers import seed_test_slot

    owner = create_user(
        db_session,
        email="owner-slot-bk@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-slot-bk@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    slot = seed_test_slot(db_session, listing=listing)

    create_resp = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id), "availability_slot_id": str(slot.id)},
    )
    assert create_resp.status_code == 201
    db_session.refresh(slot)
    assert slot.status == SlotStatus.HELD

    booking_id = create_resp.json()["id"]
    decline_resp = client.patch(
        f"/bookings/{booking_id}",
        headers=auth_header(owner),
        json={"status": "declined"},
    )
    assert decline_resp.status_code == 200
    db_session.refresh(slot)
    assert slot.status == SlotStatus.OPEN


def test_booking_with_slot_is_booked_on_approve(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    from app.models.listing_availability_slot import SlotStatus
    from tests.helpers import seed_test_slot

    owner = create_user(
        db_session,
        email="owner-slot-bk2@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-slot-bk2@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    slot = seed_test_slot(db_session, listing=listing, days_ahead=4)

    create_resp = client.post(
        "/bookings",
        headers=auth_header(rider),
        json={"listing_id": str(listing.id), "availability_slot_id": str(slot.id)},
    )
    assert create_resp.status_code == 201
    booking_id = create_resp.json()["id"]

    approve_resp = client.patch(
        f"/bookings/{booking_id}",
        headers=auth_header(owner),
        json={"status": "approved"},
    )
    assert approve_resp.status_code == 200
    db_session.refresh(slot)
    assert slot.status == SlotStatus.BOOKED
