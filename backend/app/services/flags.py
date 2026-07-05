import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking_request import BookingRequest, BookingStatus
from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.invite_token import InviteToken
from app.models.platform_flag import PlatformFlag, PlatformFlagType
from app.models.user import User

MIN_INTERACTIONS = 5
MINOR_RATIO_THRESHOLD = 0.5
WINDOW_DAYS = 90


def count_active_tokens(db: Session, owner_id: uuid.UUID) -> int:
    now = datetime.now(UTC)
    return (
        db.scalar(
            select(func.count())
            .select_from(InviteToken)
            .where(
                InviteToken.owner_id == owner_id,
                InviteToken.revoked_at.is_(None),
                InviteToken.expires_at > now,
                InviteToken.use_count < InviteToken.max_uses,
            )
        )
        or 0
    )


def count_redemptions_last_30_days(db: Session, owner_id: uuid.UUID) -> int:
    since = datetime.now(UTC) - timedelta(days=30)
    return (
        db.scalar(
            select(func.count())
            .select_from(FriendInvite)
            .where(
                FriendInvite.owner_id == owner_id,
                FriendInvite.invite_token_id.is_not(None),
                FriendInvite.created_at >= since,
            )
        )
        or 0
    )


def maybe_flag_redemption_rate(db: Session, owner_id: uuid.UUID) -> None:
    count = count_redemptions_last_30_days(db, owner_id)
    if count <= 25:
        return
    existing = db.scalar(
        select(PlatformFlag).where(
            PlatformFlag.user_id == owner_id,
            PlatformFlag.flag_type == PlatformFlagType.INVITE_REDEMPTION_RATE,
            PlatformFlag.resolved_at.is_(None),
        )
    )
    if existing is not None:
        return
    db.add(
        PlatformFlag(
            user_id=owner_id,
            flag_type=PlatformFlagType.INVITE_REDEMPTION_RATE,
            details={"redemptions_30d": count},
        )
    )


def _trainer_flagged_user(db: Session, user_id: uuid.UUID) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    if not (user.is_horse_trainer or user.is_riding_instructor):
        return None
    return user


def _count_minor_skew_interactions(db: Session, owner_id: uuid.UUID) -> tuple[int, int]:
    since = datetime.now(UTC) - timedelta(days=WINDOW_DAYS)
    invite_statuses = (
        FriendInviteStatus.ACTIVE,
        FriendInviteStatus.PENDING_OWNER_CONFIRM,
        FriendInviteStatus.PENDING_GUARDIAN,
    )
    invite_rows = db.execute(
        select(User.is_minor)
        .select_from(FriendInvite)
        .join(User, User.id == FriendInvite.rider_id)
        .where(
            FriendInvite.owner_id == owner_id,
            FriendInvite.status.in_(invite_statuses),
            FriendInvite.created_at >= since,
        )
    ).all()
    booking_rows = db.execute(
        select(User.is_minor)
        .select_from(BookingRequest)
        .join(User, User.id == BookingRequest.rider_id)
        .where(
            BookingRequest.owner_id == owner_id,
            BookingRequest.status.not_in((BookingStatus.CANCELLED, BookingStatus.DECLINED)),
            BookingRequest.requested_at >= since,
        )
    ).all()
    counterparties = [row[0] for row in invite_rows + booking_rows]
    total = len(counterparties)
    minors = sum(1 for is_minor in counterparties if is_minor)
    return total, minors


def maybe_flag_trainer_minor_skew(db: Session, user_id: uuid.UUID) -> None:
    user = _trainer_flagged_user(db, user_id)
    if user is None:
        return
    total, minors = _count_minor_skew_interactions(db, user_id)
    if total < MIN_INTERACTIONS:
        return
    ratio = minors / total
    if ratio < MINOR_RATIO_THRESHOLD:
        return
    existing = db.scalar(
        select(PlatformFlag).where(
            PlatformFlag.user_id == user_id,
            PlatformFlag.flag_type == PlatformFlagType.MINOR_INVITE_SKEW,
            PlatformFlag.resolved_at.is_(None),
        )
    )
    if existing is not None:
        return
    db.add(
        PlatformFlag(
            user_id=user_id,
            flag_type=PlatformFlagType.MINOR_INVITE_SKEW,
            details={
                "interactions_90d": total,
                "minor_count": minors,
                "minor_ratio": round(ratio, 3),
                "trainer_flags": {
                    "is_horse_trainer": user.is_horse_trainer,
                    "is_riding_instructor": user.is_riding_instructor,
                },
            },
        )
    )
