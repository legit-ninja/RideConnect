import math
import random


def jitter_coordinates(lat: float, lng: float, min_km: float = 5.0, max_km: float = 8.0) -> tuple[float, float]:
    """Offset true coordinates by at least min_km for public map display."""
    distance_km = random.uniform(min_km, max_km)
    bearing = random.uniform(0, 2 * math.pi)
    delta_lat = (distance_km / 111.0) * math.cos(bearing)
    cos_lat = math.cos(math.radians(lat)) or 1e-6
    delta_lng = (distance_km / (111.0 * cos_lat)) * math.sin(bearing)
    return lat + delta_lat, lng + delta_lng


def default_display_location(address: str | None = None) -> str:
    if address and "," in address:
        parts = [p.strip() for p in address.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-2]
    return "Appalachian NC"
