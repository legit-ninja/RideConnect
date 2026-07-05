import pytest
from fastapi import HTTPException

from app.models.user import RiderType, VerificationStatus
from app.schemas.family import FamilyMemberInput, UpdateFamilyProfileRequest
from app.services.family import apply_family_profile, validate_family_profile
from tests.conftest import create_user


def test_validate_family_requires_roster(db_session) -> None:
    user = create_user(db_session, email="family@test.com", is_rider=True)
    with pytest.raises(HTTPException) as exc:
        validate_family_profile(
            user,
            UpdateFamilyProfileRequest(
                rider_type=RiderType.FAMILY,
                family_name="Smith",
                family_size=2,
                members=None,
            ),
        )
    assert exc.value.status_code == 400


def test_apply_family_profile_creates_roster(db_session) -> None:
    user = create_user(
        db_session,
        email="family2@test.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    members = apply_family_profile(
        db_session,
        user,
        UpdateFamilyProfileRequest(
            rider_type=RiderType.FAMILY,
            family_name="Rivera",
            family_size=2,
            members=[
                FamilyMemberInput(display_name="Alex", rider_skill_level=2, is_minor=False),
                FamilyMemberInput(display_name="Sam", rider_skill_level=1, is_minor=True),
            ],
        ),
    )
    db_session.commit()
    assert user.rider_type == RiderType.FAMILY
    assert user.family_name == "Rivera"
    assert len(members) == 2
    assert members[1].is_minor is True


def test_switch_to_individual_clears_roster(db_session) -> None:
    user = create_user(
        db_session,
        email="family3@test.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    apply_family_profile(
        db_session,
        user,
        UpdateFamilyProfileRequest(
            rider_type=RiderType.FAMILY,
            family_name="Lee",
            family_size=2,
            members=[
                FamilyMemberInput(display_name="Pat", is_minor=False),
                FamilyMemberInput(display_name="Quinn", is_minor=False),
            ],
        ),
    )
    db_session.commit()
    apply_family_profile(
        db_session,
        user,
        UpdateFamilyProfileRequest(rider_type=RiderType.INDIVIDUAL),
    )
    db_session.commit()
    assert user.rider_type == RiderType.INDIVIDUAL
    assert user.family_name is None
    assert len(user.family_members) == 0
