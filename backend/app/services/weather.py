"""Daily weather forecasts via Open-Meteo (no API key). Cached in-process for MVP."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

from app.config import settings

# Open-Meteo free forecast horizon (days ahead from today, inclusive).
_OPEN_METEO_FORECAST_DAYS = 16

# Ride suitability thresholds (precip %, wind mph) — tune in one place.
_PRECIP_GOOD = 30
_PRECIP_POOR = 60
_WIND_GOOD_MPH = 20
_WIND_CAUTION_MPH = 30

_cache: dict[tuple[float, float, str, str], tuple[float, list[dict]]] = {}


@dataclass
class DailyWeather:
    date: str
    temp_max_f: float | None
    temp_min_f: float | None
    precip_probability_max: int | None
    wind_speed_max_mph: float | None
    weather_code: int | None
    ride_suitability: str
    summary: str


def _c_to_f(celsius: float | None) -> float | None:
    if celsius is None:
        return None
    return celsius * 9 / 5 + 32


def _kmh_to_mph(kmh: float | None) -> float | None:
    if kmh is None:
        return None
    return kmh * 0.621371


def ride_suitability(precip: int | None, wind_mph: float | None) -> str:
    precip = precip if precip is not None else 0
    wind = wind_mph if wind_mph is not None else 0
    if precip > _PRECIP_POOR or wind > _WIND_CAUTION_MPH:
        return "poor"
    if precip > _PRECIP_GOOD or wind > _WIND_GOOD_MPH:
        return "caution"
    return "good"


def _weather_summary(code: int | None, precip: int | None) -> str:
    if precip is not None and precip >= 50:
        return "Rain likely"
    if code is None:
        return "Forecast available"
    if code in (0, 1):
        return "Clear"
    if code in (2, 3):
        return "Partly cloudy"
    if code in (45, 48):
        return "Foggy"
    if code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "Rain"
    if code in (71, 73, 75, 85, 86):
        return "Snow"
    if code in (95, 96, 99):
        return "Storms"
    return "Mixed conditions"


def _clamp_forecast_range(from_date: date, to_date: date) -> tuple[date, date] | None:
    """Open-Meteo rejects end_date beyond ~16 days ahead; clamp instead of failing."""
    today = date.today()
    max_end = today + timedelta(days=_OPEN_METEO_FORECAST_DAYS - 1)
    if from_date > max_end:
        return None
    effective_to = min(to_date, max_end)
    return from_date, effective_to


def fetch_daily_forecast(
    lat: float,
    lng: float,
    from_date: date,
    to_date: date,
) -> list[DailyWeather]:
    clamped = _clamp_forecast_range(from_date, to_date)
    if clamped is None:
        return []
    request_from, request_to = clamped
    cache_key = (
        round(lat, 2),
        round(lng, 2),
        request_from.isoformat(),
        request_to.isoformat(),
    )
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < settings.weather_cache_ttl_seconds:
        return [_row_to_daily(row) for row in cached[1]]

    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "weather_code",
            ]
        ),
        "timezone": settings.weather_timezone,
        "start_date": request_from.isoformat(),
        "end_date": request_to.isoformat(),
        "wind_speed_unit": "kmh",
        "temperature_unit": "celsius",
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return []

    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    rows: list[dict] = []
    for index, day_str in enumerate(dates):
        precip = _safe_int(daily.get("precipitation_probability_max"), index)
        wind_mph = _kmh_to_mph(_safe_float(daily.get("wind_speed_10m_max"), index))
        code = _safe_int(daily.get("weather_code"), index)
        row = {
            "date": day_str,
            "temp_max_f": _c_to_f(_safe_float(daily.get("temperature_2m_max"), index)),
            "temp_min_f": _c_to_f(_safe_float(daily.get("temperature_2m_min"), index)),
            "precip_probability_max": precip,
            "wind_speed_max_mph": wind_mph,
            "weather_code": code,
            "ride_suitability": ride_suitability(precip, wind_mph),
            "summary": _weather_summary(code, precip),
        }
        rows.append(row)

    _cache[cache_key] = (now, rows)
    return [_row_to_daily(row) for row in rows]


def _safe_float(values: list | None, index: int) -> float | None:
    if not values or index >= len(values):
        return None
    value = values[index]
    return float(value) if value is not None else None


def _safe_int(values: list | None, index: int) -> int | None:
    if not values or index >= len(values):
        return None
    value = values[index]
    return int(value) if value is not None else None


def _row_to_daily(row: dict) -> DailyWeather:
    return DailyWeather(
        date=row["date"],
        temp_max_f=row.get("temp_max_f"),
        temp_min_f=row.get("temp_min_f"),
        precip_probability_max=row.get("precip_probability_max"),
        wind_speed_max_mph=row.get("wind_speed_max_mph"),
        weather_code=row.get("weather_code"),
        ride_suitability=row["ride_suitability"],
        summary=row["summary"],
    )


def clear_weather_cache() -> None:
    """For tests."""
    _cache.clear()
