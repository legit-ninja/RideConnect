import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_verified
from app.models.booking_request import BookingRequest, BookingStatus, PaymentType
from app.models.review import Review
from app.models.user import User
from app.schemas.review import CreateReviewRequest, ReviewResponse
from app.services.reviews import maybe_publish_reviews

router = APIRouter(tags=["reviews"])


@router.post(
    "/bookings/{booking_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    booking_id: uuid.UUID,
    payload: CreateReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
) -> ReviewResponse:
    booking = db.get(BookingRequest, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviews are only allowed for completed bookings",
        )
    if current_user.id not in (booking.rider_id, booking.owner_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a party to booking")

    existing = db.scalar(
        select(Review).where(
            Review.booking_request_id == booking_id,
            Review.reviewer_id == current_user.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already reviewed this booking",
        )

    reviewee_id = (
        booking.owner_id if current_user.id == booking.rider_id else booking.rider_id
    )
    review = Review(
        booking_request_id=booking_id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        rating=payload.rating,
        body=payload.body,
        is_friend_ride=booking.payment_type == PaymentType.FREE,
    )
    db.add(review)
    db.flush()
    maybe_publish_reviews(db, booking_id)
    db.commit()
    db.refresh(review)
    return ReviewResponse.model_validate(review)
