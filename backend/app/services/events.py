import uuid

from sqlalchemy.orm import Session

from app.models.event import Event


def log_event(
    db: Session,
    event_type: str,
    *,
    user_id: uuid.UUID | None = None,
    src: str | None = None,
    listing_slug: str | None = None,
    invite_token: str | None = None,
    payload: dict | None = None,
) -> Event:
    event = Event(
        event_type=event_type,
        user_id=user_id,
        src=src,
        listing_slug=listing_slug,
        invite_token=invite_token,
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event
