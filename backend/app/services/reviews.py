from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking_request import BookingRequest, BookingStatus
from app.models.review import Review


def maybe_publish_reviews(db: Session, booking_id) -> None:
    reviews = list(
        db.scalars(select(Review).where(Review.booking_request_id == booking_id)).all()
    )
    if not reviews:
        return
    now = datetime.now(UTC)
    parties = {booking_id}
    booking = db.get(BookingRequest, booking_id)
    if booking is None:
        return
    parties.add(booking.rider_id)
    parties.add(booking.owner_id)

    submitted = [r for r in reviews if r.published_at is None]
    if len(submitted) >= 2:
        for review in submitted:
            review.published_at = now
        return

    if len(submitted) == 1:
        first = submitted[0]
        if first.created_at + timedelta(days=14) <= now:
            first.published_at = now
