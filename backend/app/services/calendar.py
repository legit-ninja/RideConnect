from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.animal import Animal
from app.models.booking_request import BookingRequest, BookingStatus
from app.models.listing import Listing
from app.models.listing_availability_slot import ListingAvailabilitySlot, SlotStatus
from app.models.user import User
from app.schemas.availability_slot import (
    CalendarDaySummary,
    CalendarResponse,
    CalendarWeatherDay,
    OpenSlotSummary,
)
from app.schemas.booking import BookingResponse
from app.services.listings import haversine_km
from app.services.weather import DailyWeather, fetch_daily_forecast


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
        availability_slot_id=booking.availability_slot_id,
    )


def _slot_to_open_summary(slot: ListingAvailabilitySlot) -> OpenSlotSummary:
    listing = slot.listing
    return OpenSlotSummary(
        id=slot.id,
        listing_id=listing.id,
        slug=listing.slug,
        animal_name=listing.animal.name,
        activity_type=listing.activity_type.value,
        price=listing.price,
        display_location=listing.display_location,
        start_at=slot.start_at,
        end_at=slot.end_at,
    )


def _date_range(from_date: date, to_date: date) -> list[date]:
    days: list[date] = []
    current = from_date
    while current <= to_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def _slot_on_date(slot: ListingAvailabilitySlot, day: date) -> bool:
    start = slot.start_at.astimezone(UTC).date()
    return start == day


def _booking_on_date(booking: BookingRequest, day: date) -> bool:
    if booking.scheduled_at is None:
        return False
    return booking.scheduled_at.astimezone(UTC).date() == day


def get_open_slots_in_range(
    db: Session,
    *,
    from_dt: datetime,
    to_dt: datetime,
    lat: float,
    lng: float,
    radius_km: float,
) -> list[ListingAvailabilitySlot]:
    stmt = (
        select(ListingAvailabilitySlot)
        .join(Listing, ListingAvailabilitySlot.listing_id == Listing.id)
        .options(selectinload(ListingAvailabilitySlot.listing).selectinload(Listing.animal))
        .where(
            Listing.active.is_(True),
            ListingAvailabilitySlot.status == SlotStatus.OPEN,
            ListingAvailabilitySlot.start_at >= from_dt,
            ListingAvailabilitySlot.start_at <= to_dt,
        )
        .order_by(ListingAvailabilitySlot.start_at.asc())
    )
    slots = list(db.scalars(stmt).all())
    filtered: list[ListingAvailabilitySlot] = []
    for slot in slots:
        listing = slot.listing
        if haversine_km(lat, lng, listing.public_lat, listing.public_lng) <= radius_km:
            filtered.append(slot)
    return filtered


def get_user_bookings_in_range(
    db: Session,
    user: User,
    *,
    from_dt: datetime,
    to_dt: datetime,
) -> list[BookingRequest]:
    active_statuses = (
        BookingStatus.PENDING_PAYMENT,
        BookingStatus.PENDING_OWNER,
        BookingStatus.APPROVED,
        BookingStatus.COMPLETED,
    )
    stmt = (
        select(BookingRequest)
        .options(
            selectinload(BookingRequest.listing).selectinload(Listing.animal),
            selectinload(BookingRequest.rider),
            selectinload(BookingRequest.owner),
        )
        .where(
            BookingRequest.status.in_(active_statuses),
            BookingRequest.scheduled_at.isnot(None),
            BookingRequest.scheduled_at >= from_dt,
            BookingRequest.scheduled_at <= to_dt,
            or_(
                BookingRequest.rider_id == user.id,
                BookingRequest.owner_id == user.id,
            ),
        )
        .order_by(BookingRequest.scheduled_at.asc())
    )
    return list(db.scalars(stmt).all())


def build_calendar_response(
    db: Session,
    user: User,
    *,
    from_date: date,
    to_date: date,
    lat: float,
    lng: float,
    radius_km: float,
    include_open_slots: bool,
) -> CalendarResponse:
    from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=UTC)
    to_dt = datetime.combine(to_date, datetime.max.time(), tzinfo=UTC)

    open_slots: list[ListingAvailabilitySlot] = []
    if include_open_slots and user.is_rider:
        open_slots = get_open_slots_in_range(
            db,
            from_dt=from_dt,
            to_dt=to_dt,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
        )

    my_bookings = get_user_bookings_in_range(db, user, from_dt=from_dt, to_dt=to_dt)

    weather_rows: list[DailyWeather] = []
    weather_error: str | None = None
    try:
        weather_rows = fetch_daily_forecast(lat, lng, from_date, to_date)
        if not weather_rows:
            weather_error = "Weather forecast unavailable"
    except Exception:
        weather_error = "Weather forecast unavailable"

    weather_by_date = {row.date: row for row in weather_rows}

    days: list[CalendarDaySummary] = []
    for day in _date_range(from_date, to_date):
        day_str = day.isoformat()
        weather_row = weather_by_date.get(day_str)
        weather = None
        if weather_row:
            weather = CalendarWeatherDay(
                date=weather_row.date,
                temp_max_f=weather_row.temp_max_f,
                temp_min_f=weather_row.temp_min_f,
                precip_probability_max=weather_row.precip_probability_max,
                wind_speed_max_mph=weather_row.wind_speed_max_mph,
                weather_code=weather_row.weather_code,
                ride_suitability=weather_row.ride_suitability,
                summary=weather_row.summary,
            )
        days.append(
            CalendarDaySummary(
                date=day_str,
                open_slot_count=sum(1 for s in open_slots if _slot_on_date(s, day)),
                my_booking_count=sum(1 for b in my_bookings if _booking_on_date(b, day)),
                weather=weather,
            )
        )

    return CalendarResponse(
        days=days,
        open_slots=[_slot_to_open_summary(s) for s in open_slots],
        my_bookings=[_booking_to_response(b) for b in my_bookings],
        weather_error=weather_error,
    )


def get_slot_for_booking(
    db: Session, slot_id: UUID, listing_id: UUID
) -> ListingAvailabilitySlot | None:
    return db.scalar(
        select(ListingAvailabilitySlot).where(
            ListingAvailabilitySlot.id == slot_id,
            ListingAvailabilitySlot.listing_id == listing_id,
            ListingAvailabilitySlot.status == SlotStatus.OPEN,
        )
    )


def release_slot(db: Session, slot: ListingAvailabilitySlot | None) -> None:
    if slot is None:
        return
    if slot.status in (SlotStatus.HELD, SlotStatus.BOOKED):
        slot.status = SlotStatus.OPEN


def mark_slot_booked(db: Session, slot: ListingAvailabilitySlot | None) -> None:
    if slot is None:
        return
    slot.status = SlotStatus.BOOKED
