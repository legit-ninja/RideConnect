from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import require_admin, require_host, require_rider, require_verified
from app.models.booking_request import BookingRequest, BookingStatus, PaymentType
from app.models.listing import Listing
from app.models.listing_availability_slot import ListingAvailabilitySlot, SlotStatus
from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User
from app.routers.friend_invites import get_active_friend_invite
from app.schemas.booking import (
    BookingListResponse,
    BookingResponse,
    CreateBookingRequest,
    UpdateBookingStatusRequest,
)

from app.services.calendar import get_slot_for_booking, mark_slot_booked, release_slot
from app.services.events import log_event
from app.services.flags import maybe_flag_trainer_minor_skew
from app.services.rider_skill import rider_skill_warning
from app.services.threads import create_booking_thread

router = APIRouter(tags=["bookings"])

INQUIRY_NOTE_MIN_LENGTH = 10


def _thread_id_for_booking(db: Session, booking_id: UUID) -> UUID | None:
    return db.scalar(
        select(Thread.id).where(Thread.booking_request_id == booking_id)
    )


def _booking_to_response(
    db: Session, booking: BookingRequest, *, for_owner: bool = False
) -> BookingResponse:
    listing = booking.listing
    warning = None
    if for_owner:
        warning = rider_skill_warning(
            booking.rider.rider_skill_level,
            listing.min_rider_skill,
        )
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
        availability_slot_id=booking.availability_slot_id,
        note=booking.note,
        requested_at=booking.requested_at,
        listing_price=listing.price,
        activity_type=listing.activity_type.value,
        thread_id=_thread_id_for_booking(db, booking.id),
        rider_skill_warning=warning,
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

    is_inquiry = payload.availability_slot_id is None
    if is_inquiry:
        note = (payload.note or "").strip()
        if len(note) < INQUIRY_NOTE_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inquiry requires a message of at least {INQUIRY_NOTE_MIN_LENGTH} characters",
            )
    else:
        note = payload.note

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

    slot: ListingAvailabilitySlot | None = None
    scheduled_at = None
    if payload.availability_slot_id is not None:
        slot = get_slot_for_booking(db, payload.availability_slot_id, listing.id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability slot is not open for this listing",
            )
        slot_start = slot.start_at
        if slot_start.tzinfo is None:
            slot_start = slot_start.replace(tzinfo=UTC)
        if slot_start <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability slot must be in the future",
            )
        scheduled_at = slot.start_at
        initial_status = (
            BookingStatus.PENDING_OWNER
            if payment_type == PaymentType.FREE
            else BookingStatus.PENDING_PAYMENT
        )
    else:
        initial_status = BookingStatus.PENDING_OWNER

    booking = BookingRequest(
        listing_id=listing.id,
        rider_id=rider.id,
        owner_id=listing.owner_id,
        friend_invite_id=friend_invite_id,
        payment_type=payment_type,
        status=initial_status,
        scheduled_at=scheduled_at,
        availability_slot_id=payload.availability_slot_id,
        note=note,
    )
    db.add(booking)
    if slot is not None:
        slot.status = SlotStatus.HELD
    db.flush()

    thread = create_booking_thread(db, booking.id)
    message_body = (note if is_inquiry else (payload.note or "")).strip()
    if message_body:
        db.add(Message(thread_id=thread.id, sender_id=rider.id, body=message_body))

    log_event(db, "booking_requested", user_id=rider.id, payload={"booking_id": str(booking.id)})
    maybe_flag_trainer_minor_skew(db, listing.owner_id)
    db.commit()
    loaded = _load_booking(db, booking.id)
    assert loaded is not None
    return _booking_to_response(db, loaded, for_owner=False)


@router.get("/bookings", response_model=BookingListResponse)
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
    role: str = Query(default="rider", pattern="^(rider|owner)$"),
) -> BookingListResponse:
    # Authz: riders see own requests; hosts see requests for their listings.
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
        items=[
            _booking_to_response(db, b, for_owner=(role == "owner")) for b in bookings
        ],
        total=len(bookings),
    )


@router.patch("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking_status(
    booking_id: UUID,
    payload: UpdateBookingStatusRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_host),
) -> BookingResponse:
    # Authz: listing host may approve or decline pending requests.
    booking = _load_booking(db, booking_id)
    if booking is None or booking.owner_id != host.id:
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
        if booking.availability_slot_id:
            slot = db.get(ListingAvailabilitySlot, booking.availability_slot_id)
            mark_slot_booked(db, slot)
        maybe_flag_trainer_minor_skew(db, booking.owner_id)
    elif payload.status == "declined":
        booking.status = BookingStatus.DECLINED
        if booking.availability_slot_id:
            slot = db.get(ListingAvailabilitySlot, booking.availability_slot_id)
            release_slot(db, slot)
    elif payload.status == "cancelled":
        booking.status = BookingStatus.CANCELLED
        if booking.availability_slot_id:
            slot = db.get(ListingAvailabilitySlot, booking.availability_slot_id)
            release_slot(db, slot)
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
    return _booking_to_response(db, loaded, for_owner=True)


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
        items=[_booking_to_response(db, b) for b in bookings],
        total=total,
    )
