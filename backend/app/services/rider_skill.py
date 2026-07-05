from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import ModerationStatus, Review
from app.models.rider_skill import RiderSkillLevel


def rider_skill_warning(
    rider_level: int | None,
    min_level: int | None,
) -> str | None:
    if min_level is None or rider_level is None:
        return None
    if RiderSkillLevel.meets_minimum(rider_level, min_level):
        return None
    self_label = RiderSkillLevel.label(rider_level) or "Unknown"
    min_label = RiderSkillLevel.minimum_label(min_level) or "a higher level"
    return f"Rider self-reports {self_label}; your listing suggests {min_label}."


def confirmed_rider_skill(db: Session, rider_id) -> tuple[int | None, int]:
    """Mode of published owner-observed skills; requires min 2 distinct owner reviews."""
    rows = db.scalars(
        select(Review.observed_rider_skill).where(
            Review.reviewee_id == rider_id,
            Review.observed_rider_skill.is_not(None),
            Review.published_at.is_not(None),
            Review.moderation_status == ModerationStatus.APPROVED,
        )
    ).all()
    values = [v for v in rows if v is not None]
    if len(values) < 2:
        return None, len(values)
    mode_value, _ = Counter(values).most_common(1)[0]
    return mode_value, len(values)


def confirmed_rider_skill_label(db: Session, rider_id) -> str | None:
    mode, count = confirmed_rider_skill(db, rider_id)
    if mode is None or count < 2:
        return None
    label = RiderSkillLevel.label(mode)
    if label is None:
        return None
    return f"Confirmed {label} by {count} owners"
