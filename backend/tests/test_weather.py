from datetime import date
from unittest.mock import MagicMock, patch

from app.services.weather import clear_weather_cache, fetch_daily_forecast, ride_suitability


def test_ride_suitability_mapping() -> None:
    assert ride_suitability(20, 15) == "good"
    assert ride_suitability(45, 22) == "caution"
    assert ride_suitability(70, 18) == "poor"
    assert ride_suitability(10, 35) == "poor"


def test_fetch_daily_forecast_clamps_end_date_to_forecast_horizon() -> None:
    """Full calendar month must not exceed Open-Meteo's ~16-day forecast window."""
    clear_weather_cache()
    payload = {
        "daily": {
            "time": ["2026-07-05", "2026-07-10"],
            "temperature_2m_max": [30.0, 31.0],
            "temperature_2m_min": [18.0, 19.0],
            "precipitation_probability_max": [15, 20],
            "wind_speed_10m_max": [16.0, 14.0],
            "weather_code": [1, 2],
        }
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = payload
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    with patch("app.services.weather.httpx.Client", return_value=mock_client):
        with patch("app.services.weather.date") as mock_date:
            mock_date.today.return_value = date(2026, 7, 5)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            rows = fetch_daily_forecast(
                36.2,
                -81.6,
                date(2026, 7, 1),
                date(2026, 7, 31),
            )

    assert len(rows) == 2
    call_params = mock_client.get.call_args.kwargs["params"]
    assert call_params["start_date"] == "2026-07-01"
    assert call_params["end_date"] == "2026-07-20"


def test_fetch_daily_forecast_parses_open_meteo_response() -> None:
    clear_weather_cache()
    payload = {
        "daily": {
            "time": ["2026-07-10"],
            "temperature_2m_max": [30.0],
            "temperature_2m_min": [18.0],
            "precipitation_probability_max": [15],
            "wind_speed_10m_max": [16.0],
            "weather_code": [1],
        }
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = payload
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    with patch("app.services.weather.httpx.Client", return_value=mock_client):
        rows = fetch_daily_forecast(
            36.2,
            -81.6,
            date(2026, 7, 10),
            date(2026, 7, 10),
        )

    assert len(rows) == 1
    assert rows[0].date == "2026-07-10"
    assert rows[0].ride_suitability == "good"
    assert rows[0].summary == "Clear"
