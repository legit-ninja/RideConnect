from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

from app.models.booking_request import BookingRequest, BookingStatus, PaymentType
from app.models.user import VerificationStatus
from tests.helpers import seed_test_listing, seed_test_slot


def test_calendar_returns_aggregate_shape(client, db_session, horse_species) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-cal@example.com",
        is_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-cal@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    listing = seed_test_listing(db_session, horse_species=horse_species, owner=owner)
    slot = seed_test_slot(db_session, listing=listing, days_ahead=3)
    booking = BookingRequest(
        listing_id=listing.id,
        rider_id=rider.id,
        owner_id=owner.id,
        payment_type=PaymentType.PAID,
        status=BookingStatus.APPROVED,
        scheduled_at=slot.start_at,
    )
    db_session.add(booking)
    db_session.commit()

    from_date = date.today()
    to_date = from_date + timedelta(days=6)
    mock_weather = [
        type(
            "Row",
            (),
            {
                "date": from_date.isoformat(),
                "temp_max_f": 72.0,
                "temp_min_f": 55.0,
                "precip_probability_max": 10,
                "wind_speed_max_mph": 8.0,
                "weather_code": 0,
                "ride_suitability": "good",
                "summary": "Clear",
            },
        )()
    ]

    with patch(
        "app.services.calendar.fetch_daily_forecast",
        return_value=mock_weather,
    ):
        response = client.get(
            "/calendar",
            headers=auth_header(rider),
            params={"from": from_date.isoformat(), "to": to_date.isoformat()},
        )

    assert response.status_code == 200
    data = response.json()
    assert "days" in data
    assert len(data["days"]) == 7
    assert any(item["open_slot_count"] >= 1 for item in data["days"])
    assert len(data["open_slots"]) >= 1
    assert len(data["my_bookings"]) == 1
    assert data["days"][0]["weather"]["ride_suitability"] == "good"


def test_calendar_rejects_long_date_window(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    rider = create_user(
        db_session,
        email="rider-cal2@example.com",
        is_rider=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    from_date = date.today()
    to_date = from_date + timedelta(days=50)
    response = client.get(
        "/calendar",
        headers=auth_header(rider),
        params={"from": from_date.isoformat(), "to": to_date.isoformat()},
    )
    assert response.status_code == 400


def test_unverified_user_cannot_access_calendar(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    rider = create_user(
        db_session,
        email="rider-cal-unv@example.com",
        is_rider=True,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    from_date = date.today()
    to_date = from_date + timedelta(days=3)
    response = client.get(
        "/calendar",
        headers=auth_header(rider),
        params={"from": from_date.isoformat(), "to": to_date.isoformat()},
    )
    assert response.status_code == 403
