from fastapi import HTTPException, status

from app.models.riding_style import RidingStyle
from app.models.species import Species

ALLOWED_RIDING_STYLES = {member.value for member in RidingStyle}


def normalize_riding_styles(raw: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in raw:
        if value not in ALLOWED_RIDING_STYLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid riding style: {value}",
            )
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def require_horse_riding_styles(species: Species, riding_styles: list[str]) -> list[str]:
    normalized = normalize_riding_styles(riding_styles)
    if species.name == "horse" and len(normalized) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horses require at least one riding style (western, english, or therapy)",
        )
    return normalized
