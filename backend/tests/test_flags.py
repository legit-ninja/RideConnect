from datetime import UTC, datetime, timedelta

from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.platform_flag import PlatformFlag, PlatformFlagType
from app.models.user import VerificationStatus
from app.services.flags import MIN_INTERACTIONS, maybe_flag_trainer_minor_skew
from tests.conftest import create_user


def _seed_invite_counterparties(db, owner, minors: int, adults: int) -> None:
    since = datetime.now(UTC) - timedelta(days=10)
    for i in range(minors):
        rider = create_user(
            db,
            email=f"minor{i}@test.com",
            is_rider=True,
            is_minor=True,
            verification_status=VerificationStatus.VERIFIED,
        )
        db.add(
            FriendInvite(
                owner_id=owner.id,
                rider_id=rider.id,
                invitee_email=rider.email,
                status=FriendInviteStatus.ACTIVE,
                created_at=since,
            )
        )
    for i in range(adults):
        rider = create_user(
            db,
            email=f"adult{i}@test.com",
            is_rider=True,
            is_minor=False,
            verification_status=VerificationStatus.VERIFIED,
        )
        db.add(
            FriendInvite(
                owner_id=owner.id,
                rider_id=rider.id,
                invitee_email=rider.email,
                status=FriendInviteStatus.PENDING_OWNER_CONFIRM,
                created_at=since,
            )
        )
    db.commit()


def test_trainer_minor_skew_no_flag_below_threshold(db_session) -> None:
    owner = create_user(
        db_session,
        email="trainer-flag1@test.com",
        is_owner=True,
        is_riding_instructor=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    _seed_invite_counterparties(db_session, owner, minors=3, adults=1)
    maybe_flag_trainer_minor_skew(db_session, owner.id)
    db_session.commit()
    flag = db_session.query(PlatformFlag).filter_by(user_id=owner.id).first()
    assert flag is None


def test_trainer_minor_skew_flags_at_threshold(db_session) -> None:
    owner = create_user(
        db_session,
        email="trainer-flag2@test.com",
        is_owner=True,
        is_horse_trainer=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    _seed_invite_counterparties(db_session, owner, minors=3, adults=2)
    maybe_flag_trainer_minor_skew(db_session, owner.id)
    db_session.commit()
    flag = db_session.query(PlatformFlag).filter_by(user_id=owner.id).one()
    assert flag.flag_type == PlatformFlagType.MINOR_INVITE_SKEW
    assert flag.details["interactions_90d"] >= MIN_INTERACTIONS
