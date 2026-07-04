from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import require_admin, require_owner, require_rider, require_verified
from app.models.booking_request import BookingRequest, BookingStatus, PaymentType
from app.models.listing import Listing
from app.models.user import User
from app.routers.friend_invites import get_active_friend_invite
from app.schemas.booking import (
    BookingListResponse,
    BookingResponse,
    CreateBookingRequest,
    UpdateBookingStatusRequest,
)

from app.services.events import log_event

router = APIRouter(tags=["bookings"])


def _booking_to_response(booking: BookingRequest) -> BookingResponse:
    listing = booking.listing
    return BookingResponse(
        id=booking.id,
        listing_id=booking.listing_id,
        animal_name=listing.animal.name,
        rider_id=booking.rider_id,
        rider_email=booking.rider.email,
        rider_verification_status=booking.rider.verification_status.value,
        owner_id=booking.owner_id,
        owner_email=booking.owner.email,
        payment_type=booking.payment_type.value,
        status=booking.status.value,
        scheduled_at=booking.scheduled_at,
        note=booking.note,
        requested_at=booking.requested_at,
        listing_price=listing.price,
        activity_type=listing.activity_type.value,
    )


def _load_booking(db: Session, booking_id: UUID) -> BookingRequest | None:
    return db.scalar(
        select(BookingRequest)
        .options(
            selectinload(BookingRequest.listing).selectinload(Listing.animal),
            selectinload(BookingRequest.rider),
            selectinload(BookingRequest.owner),
        )
        .where(BookingRequest.id == booking_id)
    )


@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: CreateBookingRequest,
    db: Session = Depends(get_db),
    rider: User = Depends(require_rider),
) -> BookingResponse:
    # Authz: verified riders may request rides on active listings.
    if rider.is_minor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Minor accounts require a verified guardian before ride activity",
        )

    listing = db.scalar(
        select(Listing)
        .options(selectinload(Listing.animal))
        .where(Listing.id == payload.listing_id, Listing.active.is_(True))
    )
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if listing.owner_id == rider.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book your own listing",
        )

    payment_type = PaymentType.FREE if listing.friend_only_allowed else PaymentType.PAID
    friend_invite_id = None

    if payment_type == PaymentType.FREE:
        invite = get_active_friend_invite(db, listing.owner_id, rider.id)
        if invite is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verified friend connection required for this listing",
            )
        friend_invite_id = invite.id
        initial_status = BookingStatus.PENDING_OWNER
    else:
        initial_status = BookingStatus.PENDING_PAYMENT

    booking = BookingRequest(
        listing_id=listing.id,
        rider_id=rider.id,
        owner_id=listing.owner_id,
        friend_invite_id=friend_invite_id,
        payment_type=payment_type,
        status=initial_status,
        scheduled_at=payload.scheduled_at,
        note=payload.note,
    )
    db.add(booking)
    db.flush()
    log_event(db, "booking_requested", user_id=rider.id, payload={"booking_id": str(booking.id)})
    db.commit()
    loaded = _load_booking(db, booking.id)
    assert loaded is not None
    return _booking_to_response(loaded)


@router.get("/bookings", response_model=BookingListResponse)
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
    role: str = Query(default="rider", pattern="^(rider|owner)$"),
) -> BookingListResponse:
    # Authz: riders see own requests; owners see requests for their listings.
    if role == "owner":
        if not current_user.is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner access required",
            )
        stmt = select(BookingRequest).where(BookingRequest.owner_id == current_user.id)
    else:
        stmt = select(BookingRequest).where(BookingRequest.rider_id == current_user.id)

    bookings = list(
        db.scalars(
            stmt.options(
                selectinload(BookingRequest.listing).selectinload(Listing.animal),
                selectinload(BookingRequest.rider),
                selectinload(BookingRequest.owner),
            ).order_by(BookingRequest.requested_at.desc())
        ).all()
    )
    return BookingListResponse(
        items=[_booking_to_response(b) for b in bookings],
        total=len(bookings),
    )


@router.patch("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking_status(
    booking_id: UUID,
    payload: UpdateBookingStatusRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_owner),
) -> BookingResponse:
    # Authz: listing owner may approve or decline pending requests.
    booking = _load_booking(db, booking_id)
    if booking is None or booking.owner_id != owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if payload.status == "approved":
        if booking.status not in (
            BookingStatus.PENDING_OWNER,
            BookingStatus.PENDING_PAYMENT,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot be approved in current status",
            )
        booking.status = BookingStatus.APPROVED
    elif payload.status == "declined":
        booking.status = BookingStatus.DECLINED
    elif payload.status == "cancelled":
        booking.status = BookingStatus.CANCELLED
    elif payload.status == "completed":
        if booking.status != BookingStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only approved bookings can be marked completed",
            )
        booking.status = BookingStatus.COMPLETED
        booking.completed_at = datetime.now(UTC)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    db.commit()
    loaded = _load_booking(db, booking.id)
    assert loaded is not None
    return _booking_to_response(loaded)


@router.get("/admin/bookings", response_model=BookingListResponse)
def admin_list_bookings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BookingListResponse:
    # Authz: admins may view all booking requests for moderation oversight.
    total = db.scalar(select(func.count()).select_from(BookingRequest)) or 0
    bookings = list(
        db.scalars(
            select(BookingRequest)
            .options(
                selectinload(BookingRequest.listing).selectinload(Listing.animal),
                selectinload(BookingRequest.rider),
                selectinload(BookingRequest.owner),
            )
            .order_by(BookingRequest.requested_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return BookingListResponse(
        items=[_booking_to_response(b) for b in bookings],
        total=total,
    )
