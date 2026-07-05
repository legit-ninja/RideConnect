from datetime import UTC, datetime

from app.models.rider_skill import RiderSkillLevel
from app.models.review import ModerationStatus, Review
from app.services.rider_skill import confirmed_rider_skill_label, rider_skill_warning


def test_rider_skill_ordering() -> None:
    assert RiderSkillLevel.meets_minimum(1, 3) is False
    assert RiderSkillLevel.meets_minimum(3, 3) is True
    assert RiderSkillLevel.meets_minimum(4, 3) is True
    assert RiderSkillLevel.meets_minimum(None, 3) is True


def test_rider_skill_warning_when_below_minimum() -> None:
    warning = rider_skill_warning(1, 3)
    assert warning is not None
    assert "Beginner" in warning
    assert "Intermediate" in warning


def test_rider_skill_warning_absent_when_null() -> None:
    assert rider_skill_warning(None, 3) is None
    assert rider_skill_warning(2, None) is None


def test_confirmed_skill_requires_two_observations(
    db_session, horse_species
) -> None:
    from uuid import uuid4

    from app.models.booking_request import BookingRequest, BookingStatus, PaymentType
    from tests.conftest import create_user
    from tests.helpers import seed_test_listing

    rider = create_user(db_session, email="rider-skill@test.com", is_rider=True)
    owner1 = create_user(db_session, email="owner1-skill@test.com", is_owner=True)
    owner2 = create_user(db_session, email="owner2-skill@test.com", is_owner=True)
    listing1 = seed_test_listing(db_session, horse_species=horse_species, owner=owner1)
    listing2 = seed_test_listing(db_session, horse_species=horse_species, owner=owner2)

    booking1 = BookingRequest(
        listing_id=listing1.id,
        rider_id=rider.id,
        owner_id=owner1.id,
        payment_type=PaymentType.PAID,
        status=BookingStatus.COMPLETED,
    )
    booking2 = BookingRequest(
        listing_id=listing2.id,
        rider_id=rider.id,
        owner_id=owner2.id,
        payment_type=PaymentType.PAID,
        status=BookingStatus.COMPLETED,
    )
    db_session.add_all([booking1, booking2])
    db_session.flush()

    db_session.add(
        Review(
            booking_request_id=booking1.id,
            reviewer_id=owner1.id,
            reviewee_id=rider.id,
            rating=5,
            observed_rider_skill=3,
            published_at=datetime.now(UTC),
            moderation_status=ModerationStatus.APPROVED,
        )
    )
    db_session.commit()
    assert confirmed_rider_skill_label(db_session, rider.id) is None

    db_session.add(
        Review(
            booking_request_id=booking2.id,
            reviewer_id=owner2.id,
            reviewee_id=rider.id,
            rating=4,
            observed_rider_skill=3,
            published_at=datetime.now(UTC),
            moderation_status=ModerationStatus.APPROVED,
        )
    )
    db_session.commit()
    label = confirmed_rider_skill_label(db_session, rider.id)
    assert label is not None
    assert "Intermediate" in label
