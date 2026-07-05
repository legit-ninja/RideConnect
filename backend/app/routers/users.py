import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_verified
from app.models.booking_request import BookingRequest, BookingStatus
from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.rider_skill import RiderSkillLevel
from app.models.user import User
from app.schemas.counterparty import CounterpartyProfile
from app.services.rider_skill import confirmed_rider_skill_label

router = APIRouter(prefix="/users", tags=["users"])


def _has_counterparty_relationship(db: Session, viewer_id: uuid.UUID, target_id: uuid.UUID) -> bool:
    booking_exists = db.scalar(
        select(BookingRequest.id)
        .where(
            or_(
                (
                    (BookingRequest.rider_id == viewer_id)
                    & (BookingRequest.owner_id == target_id)
                ),
                (
                    (BookingRequest.rider_id == target_id)
                    & (BookingRequest.owner_id == viewer_id)
                ),
            ),
            BookingRequest.status.in_(
                (
                    BookingStatus.APPROVED,
                    BookingStatus.COMPLETED,
                    BookingStatus.PENDING_OWNER,
                    BookingStatus.PENDING_PAYMENT,
                )
            ),
        )
        .limit(1)
    )
    if booking_exists is not None:
        return True
    invite_exists = db.scalar(
        select(FriendInvite.id)
        .where(
            or_(
                (
                    (FriendInvite.owner_id == viewer_id)
                    & (FriendInvite.rider_id == target_id)
                ),
                (
                    (FriendInvite.owner_id == target_id)
                    & (FriendInvite.rider_id == viewer_id)
                ),
            ),
            FriendInvite.status == FriendInviteStatus.ACTIVE,
        )
        .limit(1)
    )
    return invite_exists is not None


def _trainer_labels(user: User) -> list[str]:
    labels: list[str] = []
    if user.is_horse_trainer:
        labels.append("Self-reported: Horse trainer")
    if user.is_riding_instructor:
        labels.append("Self-reported: Riding instructor")
    return labels


@router.get("/{user_id}/counterparty", response_model=CounterpartyProfile)
def get_counterparty_profile(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
) -> CounterpartyProfile:
    # Authz: verified users may view skill/trainer self-reports only for active connections.
    if user_id == current_user.id:
        target = current_user
    else:
        if not _has_counterparty_relationship(db, current_user.id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not connected to this user",
            )
        target = db.get(User, user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    last_initial = target.last_name[:1].upper() if target.last_name else ""
    return CounterpartyProfile(
        id=target.id,
        first_name=target.first_name,
        last_initial=last_initial,
        self_reported_skill_label=RiderSkillLevel.self_reported_label(target.rider_skill_level),
        confirmed_skill_label=confirmed_rider_skill_label(db, target.id),
        is_horse_trainer=target.is_horse_trainer,
        is_riding_instructor=target.is_riding_instructor,
        trainer_verified=target.trainer_verified,
        trainer_self_report_labels=_trainer_labels(target),
    )
