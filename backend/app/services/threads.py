import uuid

from sqlalchemy.orm import Session

from app.models.thread import Thread


def create_friend_invite_thread(db: Session, friend_invite_id: uuid.UUID) -> Thread:
    thread = Thread(friend_invite_id=friend_invite_id)
    db.add(thread)
    db.flush()
    return thread


def create_booking_thread(db: Session, booking_request_id: uuid.UUID) -> Thread:
    thread = Thread(booking_request_id=booking_request_id)
    db.add(thread)
    db.flush()
    return thread
