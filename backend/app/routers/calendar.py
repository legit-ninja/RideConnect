from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import require_verified
from app.models.user import User
from app.schemas.availability_slot import CalendarResponse
from app.services.calendar import build_calendar_response

router = APIRouter(tags=["calendar"])

MAX_CALENDAR_DAYS = 42


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    radius_km: float | None = Query(default=None, gt=0),
    include_open_slots: bool = Query(default=True),
    db: Session = Depends(get_db),
    user: User = Depends(require_verified),
) -> CalendarResponse:
    # Authz: verified users may view personal schedule; riders may discover open slots.
    if user.is_minor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Minor accounts require a verified guardian before ride activity",
        )

    if to_date < from_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'to' must be on or after 'from'",
        )
    if (to_date - from_date).days + 1 > MAX_CALENDAR_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Date range may not exceed {MAX_CALENDAR_DAYS} days",
        )

    return build_calendar_response(
        db,
        user,
        from_date=from_date,
        to_date=to_date,
        lat=lat if lat is not None else settings.search_default_lat,
        lng=lng if lng is not None else settings.search_default_lng,
        radius_km=radius_km if radius_km is not None else settings.search_default_radius_km,
        include_open_slots=include_open_slots and user.is_rider,
    )
