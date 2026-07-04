from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user_optional
from app.models.user import User
from app.schemas.event import CreateEventRequest
from app.services.events import log_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def create_event(
    payload: CreateEventRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> None:
    log_event(
        db,
        payload.event_type,
        user_id=current_user.id if current_user else None,
        src=payload.src,
        listing_slug=payload.listing_slug,
        invite_token=payload.invite_token,
        payload=payload.payload,
    )
    db.commit()
