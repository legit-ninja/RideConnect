import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.friend_invite import FriendInvite
from app.models.invite_token import InviteToken
from app.models.platform_flag import PlatformFlag, PlatformFlagType


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
