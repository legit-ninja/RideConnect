from datetime import UTC, datetime, timedelta

from app.models.listing_availability_slot import SlotStatus
from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing, seed_test_slot


def test_owner_lists_and_creates_slots(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-slots@example.com",
        is_owner=True,
        is_rider=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    start_at = datetime.now(UTC) + timedelta(days=4, hours=10)
    end_at = start_at + timedelta(hours=2)

    create_resp = client.post(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(owner),
        json={"start_at": start_at.isoformat(), "end_at": end_at.isoformat()},
    )
    assert create_resp.status_code == 201
    slot = create_resp.json()
    assert slot["status"] == "open"

    list_resp = client.get(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(owner),
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_non_owner_cannot_manage_slots(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-slots2@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    other_owner = create_user(
        db_session,
        email="other-owner-slots@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    slot = seed_test_slot(db_session, listing=listing)
    start_at = datetime.now(UTC) + timedelta(days=5, hours=11)
    end_at = start_at + timedelta(hours=2)

    assert (
        client.get(
            f"/owner/listings/{listing.id}/slots",
            headers=auth_header(other_owner),
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/owner/listings/{listing.id}/slots",
            headers=auth_header(other_owner),
            json={"start_at": start_at.isoformat(), "end_at": end_at.isoformat()},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/owner/listings/{listing.id}/slots/{slot.id}",
            headers=auth_header(other_owner),
            json={"status": "blocked"},
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/owner/listings/{listing.id}/slots/{slot.id}",
            headers=auth_header(other_owner),
        ).status_code
        == 404
    )


def test_owner_blocks_and_deletes_open_slot(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-slots3@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    slot = seed_test_slot(db_session, listing=listing)

    block_resp = client.patch(
        f"/owner/listings/{listing.id}/slots/{slot.id}",
        headers=auth_header(owner),
        json={"status": "blocked"},
    )
    assert block_resp.status_code == 200
    assert block_resp.json()["status"] == "blocked"

    delete_resp = client.delete(
        f"/owner/listings/{listing.id}/slots/{slot.id}",
        headers=auth_header(owner),
    )
    assert delete_resp.status_code == 204

    remaining = client.get(
        f"/owner/listings/{listing.id}/slots",
        headers=auth_header(owner),
    ).json()
    assert remaining == []
