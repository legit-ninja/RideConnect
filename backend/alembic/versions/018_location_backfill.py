"""Recompute public_lat/public_lng and display_location deterministically.

Revision ID: 018_location_backfill
Revises: 017_review_observed_skill
Create Date: 2026-07-05
"""

import hashlib
import math
import os
import re
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_location_backfill"
down_revision: Union[str, None] = "017_review_observed_skill"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

_STREET_SUFFIX = re.compile(
    r"\b("
    r"rd|road|ln|lane|dr|drive|hwy|highway|trl|trail|st|street|ave|avenue|ct|court|way"
    r")\b",
    re.IGNORECASE,
)
_ZIP_ONLY = re.compile(r"^\d{5}(-\d{4})?$")
_STATE_ABBR = re.compile(r"^[A-Z]{2}$")
_FALLBACK_DISPLAY = "Appalachian NC"


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


def _default_display_location(address: str | None) -> str:
    if not address or "," not in address:
        return _FALLBACK_DISPLAY
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) < 2:
        return _FALLBACK_DISPLAY
    if len(parts) == 2 and _looks_like_street(parts[0]):
        return _FALLBACK_DISPLAY
    for segment in reversed(parts):
        if _is_skippable_segment(segment):
            continue
        return segment
    return _FALLBACK_DISPLAY


def _deterministic_jitter(animal_id: str, lat: float, lng: float, secret: str) -> tuple[float, float]:
    digest = hashlib.sha256(f"{animal_id}{secret}".encode()).hexdigest()
    bearing = (int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)) * 2 * math.pi
    distance_km = 5.0 + (int(digest[16:24], 16) / float(0xFFFFFFFF)) * 3.0
    delta_lat = (distance_km / 111.0) * math.cos(bearing)
    cos_lat = math.cos(math.radians(lat)) or 1e-6
    delta_lng = (distance_km / (111.0 * cos_lat)) * math.sin(bearing)
    return lat + delta_lat, lng + delta_lng


def upgrade() -> None:
    secret = os.environ.get("LOCATION_JITTER_SECRET", "dev-change-me")
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT l.id, l.animal_id, a.lat, a.lng, a.address
            FROM listings l
            JOIN animals a ON a.id = l.animal_id
            """
        )
    ).fetchall()
    for listing_id, animal_id, lat, lng, address in rows:
        pub_lat, pub_lng = _deterministic_jitter(str(animal_id), float(lat), float(lng), secret)
        display = _default_display_location(address)
        bind.execute(
            sa.text(
                """
                UPDATE listings
                SET public_lat = :pub_lat,
                    public_lng = :pub_lng,
                    display_location = :display_location
                WHERE id = :id
                """
            ),
            {
                "id": str(listing_id),
                "pub_lat": pub_lat,
                "pub_lng": pub_lng,
                "display_location": display,
            },
        )


def downgrade() -> None:
    pass
