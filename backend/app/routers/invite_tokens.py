import secrets
import uuid
from datetime import UTC, datetime, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import get_db
from app.dependencies import require_owner, require_verified
from app.models.animal import Animal
from app.models.friend_invite import FriendInvite, FriendInviteStatus
from app.models.invite_token import InviteToken
from app.models.listing import Listing
from app.models.listing_photo import ListingPhoto
from app.models.review import ModerationStatus
from app.models.user import User, VerificationStatus
from app.schemas.invite_token import (
    ConfirmInviteRequest,
    CreateInviteTokenRequest,
    InviteTokenListResponse,
    InviteTokenResponse,
)
from app.schemas.public_listing import PublicInvitePreview
from app.services.events import log_event
from app.services.flags import count_active_tokens, maybe_flag_redemption_rate
from app.services.notifications import create_notification
from app.services.public_listing import get_listing_by_slug
from app.services.storage import get_public_url, put_object
from app.services.threads import create_friend_invite_thread

router = APIRouter(tags=["invite-tokens"])

FRONTEND_BASE = settings.frontend_base_url


def _share_url(token: str) -> str:
    return f"{FRONTEND_BASE}/i/{token}"


def _token_response(row: InviteToken) -> InviteTokenResponse:
    return InviteTokenResponse(
        id=row.id,
        token=row.token,
        animal_id=row.animal_id,
        max_uses=row.max_uses,
        use_count=row.use_count,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
        share_url=_share_url(row.token),
    )


@router.post(
    "/invites/tokens",
    response_model=InviteTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invite_token(
    payload: CreateInviteTokenRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> InviteTokenResponse:
    if count_active_tokens(db, owner.id) >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum active invite tokens reached",
        )
    if payload.animal_id is not None:
        animal = db.scalar(
            select(Animal).where(Animal.id == payload.animal_id, Animal.owner_id == owner.id)
        )
        if animal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")

    token_value = secrets.token_urlsafe(24)
    expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)
    row = InviteToken(
        owner_id=owner.id,
        animal_id=payload.animal_id,
        token=token_value,
        max_uses=payload.max_uses,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _token_response(row)


@router.get("/invites/tokens", response_model=InviteTokenListResponse)
def list_invite_tokens(
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> InviteTokenListResponse:
    rows = list(
        db.scalars(
            select(InviteToken)
            .where(InviteToken.owner_id == owner.id)
            .order_by(InviteToken.created_at.desc())
        ).all()
    )
    return InviteTokenListResponse(items=[_token_response(r) for r in rows])


@router.delete("/invites/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite_token(
    token_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> None:
    row = db.get(InviteToken, token_id)
    if row is None or row.owner_id != owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    row.revoked_at = datetime.now(UTC)
    db.commit()


@router.get("/public/invites/{token}", response_model=PublicInvitePreview)
def get_public_invite(
    token: str,
    db: Session = Depends(get_db),
    src: str | None = None,
) -> PublicInvitePreview:
    row = db.scalar(
        select(InviteToken)
        .options(selectinload(InviteToken.owner), selectinload(InviteToken.animal))
        .where(InviteToken.token == token)
    )
    log_event(db, "invite_landing_view", invite_token=token, src=src)
    db.commit()

    if row is None:
        return PublicInvitePreview(
            owner_first_name="",
            owner_verified=False,
            animal_names=[],
            token_valid=False,
        )

    now = datetime.now(UTC)
    expired = row.expires_at <= now
    revoked = row.revoked_at is not None
    exhausted = row.use_count >= row.max_uses
    valid = not expired and not revoked and not exhausted

    animal_names: list[str] = []
    if row.animal is not None:
        animal_names = [row.animal.name]
    elif valid:
        animals = list(
            db.scalars(select(Animal).where(Animal.owner_id == row.owner_id)).all()
        )
        animal_names = [a.name for a in animals]

    return PublicInvitePreview(
        owner_first_name=row.owner.first_name,
        owner_verified=row.owner.verification_status == VerificationStatus.VERIFIED,
        animal_names=animal_names,
        token_valid=valid,
        expired=expired,
        revoked=revoked,
    )


@router.post("/invites/tokens/{token}/redeem", response_model=dict)
def redeem_invite_token(
    token: str,
    db: Session = Depends(get_db),
    rider: User = Depends(require_verified),
) -> dict:
    if rider.is_minor and rider.guardian_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Minor accounts require a verified guardian",
        )

    now = datetime.now(UTC)
    result = db.execute(
        update(InviteToken)
        .where(
            InviteToken.token == token,
            InviteToken.use_count < InviteToken.max_uses,
            InviteToken.revoked_at.is_(None),
            InviteToken.expires_at > now,
        )
        .values(use_count=InviteToken.use_count + 1)
        .returning(InviteToken.id, InviteToken.owner_id, InviteToken.animal_id)
    ).first()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token is invalid or exhausted",
        )

    token_id, owner_id, _animal_id = result
    owner = db.get(User, owner_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    if rider.is_minor:
        invite_status = FriendInviteStatus.PENDING_GUARDIAN
    else:
        invite_status = FriendInviteStatus.PENDING_OWNER_CONFIRM

    invite = FriendInvite(
        owner_id=owner_id,
        rider_id=rider.id,
        invite_token_id=token_id,
        invitee_email=rider.email,
        status=invite_status,
        accepted_at=datetime.now(UTC),
    )
    db.add(invite)
    db.flush()

    rider_name = f"{rider.first_name} {rider.last_name}".strip() or rider.email
    create_notification(
        db,
        owner_id,
        "invite_redeemed",
        f"{rider_name} redeemed your invite link",
        {"friend_invite_id": str(invite.id), "rider_id": str(rider.id)},
    )
    maybe_flag_redemption_rate(db, owner_id)
    db.commit()
    return {"friend_invite_id": str(invite.id), "status": invite.status.value}


@router.post("/invites/{invite_id}/confirm")
def confirm_invite(
    invite_id: uuid.UUID,
    payload: ConfirmInviteRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> dict:
    invite = db.get(FriendInvite, invite_id)
    if invite is None or invite.owner_id != owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")

    if invite.status not in (
        FriendInviteStatus.PENDING_OWNER_CONFIRM,
        FriendInviteStatus.PENDING_GUARDIAN,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite cannot be confirmed in current status",
        )

    if payload.action == "decline":
        invite.status = FriendInviteStatus.DECLINED
        if invite.rider_id:
            create_notification(
                db,
                invite.rider_id,
                "invite_declined",
                f"{owner.first_name} declined your friend invite",
                {"friend_invite_id": str(invite.id)},
            )
        db.commit()
        return {"status": invite.status.value}

    if invite.status == FriendInviteStatus.PENDING_GUARDIAN:
        rider = db.get(User, invite.rider_id) if invite.rider_id else None
        if rider is None or rider.guardian_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardian approval required",
            )
        if invite.guardian_approved_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardian has not approved this connection",
            )

    invite.status = FriendInviteStatus.ACTIVE
    invite.owner_confirmed_at = datetime.now(UTC)
    create_friend_invite_thread(db, invite.id)

    if invite.rider_id:
        create_notification(
            db,
            invite.rider_id,
            "invite_confirmed",
            f"{owner.first_name} confirmed your friend connection",
            {"friend_invite_id": str(invite.id)},
        )
    db.commit()
    return {"status": invite.status.value, "thread_created": True}


@router.post("/invites/{invite_id}/guardian-approve")
def guardian_approve_invite(
    invite_id: uuid.UUID,
    db: Session = Depends(get_db),
    guardian: User = Depends(require_verified),
) -> dict:
    invite = db.get(FriendInvite, invite_id)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.status != FriendInviteStatus.PENDING_GUARDIAN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is not awaiting guardian approval",
        )
    rider = db.get(User, invite.rider_id) if invite.rider_id else None
    if rider is None or rider.guardian_user_id != guardian.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the rider guardian")

    invite.guardian_approved_at = datetime.now(UTC)
    create_notification(
        db,
        invite.owner_id,
        "guardian_approved",
        f"Guardian approved connection for {rider.first_name}",
        {"friend_invite_id": str(invite.id)},
    )
    db.commit()
    return {"status": invite.status.value, "guardian_approved_at": invite.guardian_approved_at.isoformat()}


@router.post(
    "/owner/listings/{listing_id}/photos",
    status_code=status.HTTP_201_CREATED,
)
async def upload_listing_photo(
    listing_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> dict:
    listing = db.scalar(
        select(Listing).where(Listing.id == listing_id, Listing.owner_id == owner.id)
    )
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    raw = await file.read()
    image = Image.open(BytesIO(raw))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    primary_buf = BytesIO()
    image.save(primary_buf, format="JPEG", exif=b"")
    primary_key = f"listings/{listing_id}/{uuid.uuid4()}.jpg"
    put_object(primary_key, primary_buf.getvalue())

    thumb = image.copy()
    thumb.thumbnail((400, 400))
    thumb_buf = BytesIO()
    thumb.save(thumb_buf, format="JPEG", exif=b"")
    thumb_key = f"listings/{listing_id}/{uuid.uuid4()}_thumb.jpg"
    put_object(thumb_key, thumb_buf.getvalue())

    moderation = (
        ModerationStatus.PENDING
        if settings.photo_moderation_enabled
        else ModerationStatus.APPROVED
    )
    photo = ListingPhoto(
        listing_id=listing_id,
        storage_key=primary_key,
        thumbnail_key=thumb_key,
        moderation_status=moderation,
        is_primary=False,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {
        "id": str(photo.id),
        "url": get_public_url(primary_key),
        "thumbnail_url": get_public_url(thumb_key),
    }
