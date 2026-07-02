from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_owner, require_rider, require_verified
from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.user import User, VerificationStatus
from app.schemas.friend_invite import (
    CreateFriendInviteRequest,
    FriendInviteListResponse,
    FriendInviteResponse,
    UpdateFriendInviteStatusRequest,
)

router = APIRouter(tags=["friend-invites"])


def _invite_to_response(invite: FriendInvite) -> FriendInviteResponse:
    return FriendInviteResponse(
        id=invite.id,
        owner_id=invite.owner_id,
        rider_id=invite.rider_id,
        invitee_email=invite.invitee_email,
        status=invite.status.value,
        invited_at=invite.invited_at,
        accepted_at=invite.accepted_at,
        created_at=invite.created_at,
    )


@router.post(
    "/owner/friend-invites",
    response_model=FriendInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_friend_invite(
    payload: CreateFriendInviteRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> FriendInviteResponse:
    # Authz: verified owners may invite specific riders by email (pairwise, not platform-wide).
    email = payload.invitee_email.lower().strip()
    if email == owner.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite yourself",
        )

    existing = db.scalar(
        select(FriendInvite).where(
            FriendInvite.owner_id == owner.id,
            func.lower(FriendInvite.invitee_email) == email,
            FriendInvite.status == FriendInviteStatus.PENDING,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending invite already exists for this email",
        )

    rider = db.scalar(select(User).where(func.lower(User.email) == email))
    rider_id = rider.id if rider else None
    if rider is not None and rider.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitee must complete identity verification before accepting",
        )

    invite = FriendInvite(
        owner_id=owner.id,
        rider_id=rider_id,
        invitee_email=email,
        status=FriendInviteStatus.PENDING,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


@router.get("/owner/friend-invites", response_model=FriendInviteListResponse)
def list_owner_friend_invites(
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> FriendInviteListResponse:
    # Authz: owners see invites they sent.
    invites = list(
        db.scalars(
            select(FriendInvite)
            .where(FriendInvite.owner_id == owner.id)
            .order_by(FriendInvite.created_at.desc())
        ).all()
    )
    return FriendInviteListResponse(items=[_invite_to_response(i) for i in invites])


@router.patch(
    "/owner/friend-invites/{invite_id}",
    response_model=FriendInviteResponse,
)
def owner_update_friend_invite(
    invite_id: UUID,
    payload: UpdateFriendInviteStatusRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> FriendInviteResponse:
    # Authz: owners may cancel their own pending invites.
    invite = db.get(FriendInvite, invite_id)
    if invite is None or invite.owner_id != owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if payload.status != "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners may only cancel invites",
        )
    if invite.status != FriendInviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is no longer pending",
        )
    invite.status = FriendInviteStatus.CANCELLED
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


@router.get("/rider/friend-invites", response_model=FriendInviteListResponse)
def list_rider_friend_invites(
    db: Session = Depends(get_db),
    rider: User = Depends(require_rider),
) -> FriendInviteListResponse:
    # Authz: riders see invites addressed to their account email.
    invites = list(
        db.scalars(
            select(FriendInvite).where(
                (FriendInvite.rider_id == rider.id)
                | (func.lower(FriendInvite.invitee_email) == rider.email.lower())
            ).order_by(FriendInvite.created_at.desc())
        ).all()
    )
    return FriendInviteListResponse(items=[_invite_to_response(i) for i in invites])


@router.patch(
    "/rider/friend-invites/{invite_id}/respond",
    response_model=FriendInviteResponse,
)
def rider_respond_friend_invite(
    invite_id: UUID,
    payload: UpdateFriendInviteStatusRequest,
    db: Session = Depends(get_db),
    rider: User = Depends(require_rider),
) -> FriendInviteResponse:
    # Authz: verified riders may accept or decline invites sent to them.
    if payload.status not in ("accepted", "declined"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Riders may only accept or decline",
        )
    invite = db.get(FriendInvite, invite_id)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.rider_id not in (None, rider.id) and invite.invitee_email.lower() != rider.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your invite")
    if invite.status != FriendInviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is no longer pending",
        )
    invite.rider_id = rider.id
    invite.status = (
        FriendInviteStatus.ACCEPTED
        if payload.status == "accepted"
        else FriendInviteStatus.DECLINED
    )
    if payload.status == "accepted":
        invite.accepted_at = datetime.now(UTC)
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


def get_accepted_friend_invite(
    db: Session, owner_id: UUID, rider_id: UUID
) -> FriendInvite | None:
    return db.scalar(
        select(FriendInvite).where(
            FriendInvite.owner_id == owner_id,
            FriendInvite.rider_id == rider_id,
            FriendInvite.status == FriendInviteStatus.ACCEPTED,
        )
    )
