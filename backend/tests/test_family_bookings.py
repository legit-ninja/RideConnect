from decimal import Decimal

from app.models.user import RiderType, VerificationStatus
from app.schemas.family import FamilyMemberInput, UpdateFamilyProfileRequest
from app.services.family import apply_family_profile
from tests.conftest import auth_header, create_user
from tests.helpers import seed_test_listing, seed_test_slot


def test_family_booking_creates_group(db_session, horse_species, client) -> None:
    owner = create_user(
        db_session,
        email="family-owner@test.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="family-rider@test.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    apply_family_profile(
        db_session,
        rider,
        UpdateFamilyProfileRequest(
            rider_type=RiderType.FAMILY,
            family_name="Test Family",
            family_size=2,
            members=[
                FamilyMemberInput(display_name="Parent", rider_skill_level=3),
                FamilyMemberInput(display_name="Child", rider_skill_level=1, is_minor=True),
            ],
        ),
    )
    db_session.commit()
    member_ids = [m.id for m in rider.family_members]

    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    slot = seed_test_slot(db_session, listing=listing)

    response = client.post(
        "/bookings",
        json={
            "listing_id": str(listing.id),
            "availability_slot_id": str(slot.id),
            "family_member_ids": [str(mid) for mid in member_ids],
        },
        headers=auth_header(rider),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["is_family_booking"] is True
    assert body["family_party_size"] == 2
    assert body["booker_family_name"] == "Test Family"

    owner_list = client.get("/bookings?role=owner", headers=auth_header(owner))
    assert owner_list.status_code == 200
    items = owner_list.json()["items"]
    assert len(items) == 1
    assert items[0]["family_party_size"] == 2
    assert len(items[0]["family_participants"]) == 2


def test_family_booking_requires_roster_members(db_session, horse_species, client) -> None:
    owner = create_user(
        db_session,
        email="family-owner2@test.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="family-rider2@test.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    apply_family_profile(
        db_session,
        rider,
        UpdateFamilyProfileRequest(
            rider_type=RiderType.FAMILY,
            family_name="Empty",
            family_size=2,
            members=[
                FamilyMemberInput(display_name="A"),
                FamilyMemberInput(display_name="B"),
            ],
        ),
    )
    db_session.commit()
    listing = seed_test_listing(
        db_session,
        horse_species=horse_species,
        owner=owner,
        price=Decimal("40.00"),
    )

    response = client.post(
        "/bookings",
        json={"listing_id": str(listing.id), "note": "We would like a weekend lesson please"},
        headers=auth_header(rider),
    )
    assert response.status_code == 400
