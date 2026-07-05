import hashlib
import math
import re
from uuid import UUID

_FALLBACK_DISPLAY = "Appalachian NC"

# Word-boundary road suffixes (case-insensitive).
_STREET_SUFFIX = re.compile(
    r"\b("
    r"rd|road|ln|lane|dr|drive|hwy|highway|trl|trail|st|street|ave|avenue|ct|court|way"
    r")\b",
    re.IGNORECASE,
)

_ZIP_ONLY = re.compile(r"^\d{5}(-\d{4})?$")
_STATE_ABBR = re.compile(r"^[A-Z]{2}$")


def _looks_like_street(segment: str) -> bool:
    if not segment:
        return True
    if segment.upper().startswith("PO BOX"):
        return True
    if any(ch.isdigit() for ch in segment):
        return True
    return _STREET_SUFFIX.search(segment) is not None


def _is_skippable_segment(segment: str) -> bool:
    if _ZIP_ONLY.match(segment):
        return True
    if _STATE_ABBR.match(segment):
        return True
    return _looks_like_street(segment)


def default_display_location(address: str | None = None) -> str:
    """Pick a public-safe location label from a comma-separated address."""
    if not address or "," not in address:
        return _FALLBACK_DISPLAY

    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) < 2:
        return _FALLBACK_DISPLAY

    # Two-part "street, zip/city" addresses are ambiguous — never expose the street line.
    if len(parts) == 2 and _looks_like_street(parts[0]):
        return _FALLBACK_DISPLAY

    for segment in reversed(parts):
        if _is_skippable_segment(segment):
            continue
        return segment

    return _FALLBACK_DISPLAY


def deterministic_jitter(
    animal_id: UUID,
    lat: float,
    lng: float,
    secret: str,
    min_km: float = 5.0,
    max_km: float = 8.0,
) -> tuple[float, float]:
    """Stable offset per animal for public map display (5–8 km band)."""
    digest = hashlib.sha256(f"{animal_id}{secret}".encode()).hexdigest()
    bearing = (int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)) * 2 * math.pi
    distance_km = min_km + (int(digest[16:24], 16) / float(0xFFFFFFFF)) * (max_km - min_km)
    delta_lat = (distance_km / 111.0) * math.cos(bearing)
    cos_lat = math.cos(math.radians(lat)) or 1e-6
    delta_lng = (distance_km / (111.0 * cos_lat)) * math.sin(bearing)
    return lat + delta_lat, lng + delta_lng


def jitter_coordinates(
    animal_id: UUID,
    lat: float,
    lng: float,
    secret: str,
    min_km: float = 5.0,
    max_km: float = 8.0,
) -> tuple[float, float]:
    """Alias for deterministic jitter (per-animal stable point)."""
    return deterministic_jitter(animal_id, lat, lng, secret, min_km, max_km)
