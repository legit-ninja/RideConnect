from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import require_verified
from app.models.booking_request import BookingRequest
from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User
from app.schemas.message import CreateMessageRequest, MessageListResponse, MessageResponse
from app.services.events import log_event

router = APIRouter(tags=["threads"])


def _get_thread_with_booking(db: Session, thread_id: UUID) -> Thread | None:
    return db.scalar(
        select(Thread)
        .options(
            selectinload(Thread.messages),
        )
        .where(Thread.id == thread_id)
    )


def _get_booking_for_thread(db: Session, thread: Thread) -> BookingRequest | None:
    if thread.booking_request_id is None:
        return None
    return db.scalar(
        select(BookingRequest)
        .options(selectinload(BookingRequest.listing))
        .where(BookingRequest.id == thread.booking_request_id)
    )


def _assert_thread_participant(booking: BookingRequest, user: User) -> None:
    # Authz: only the rider or listing host may read/post in a booking thread.
    if user.id == booking.rider_id or user.id == booking.owner_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/threads/{thread_id}/messages", response_model=MessageListResponse)
def list_thread_messages(
    thread_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_verified),
) -> MessageListResponse:
    thread = _get_thread_with_booking(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    booking = _get_booking_for_thread(db, thread)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    _assert_thread_participant(booking, user)

    messages = list(
        db.scalars(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.sent_at.asc())
        ).all()
    )
    return MessageListResponse(
        items=[MessageResponse.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.post(
    "/threads/{thread_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_thread_message(
    thread_id: UUID,
    payload: CreateMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_verified),
) -> MessageResponse:
    thread = _get_thread_with_booking(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    booking = _get_booking_for_thread(db, thread)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    _assert_thread_participant(booking, user)

    message = Message(thread_id=thread.id, sender_id=user.id, body=payload.body.strip())
    db.add(message)
    db.flush()
    log_event(
        db,
        "message_sent",
        user_id=user.id,
        payload={"thread_id": str(thread.id), "message_id": str(message.id)},
    )
    db.commit()
    db.refresh(message)
    return MessageResponse.model_validate(message)
