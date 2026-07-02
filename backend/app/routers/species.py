from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.species import Species
from app.schemas.species import SpeciesResponse

router = APIRouter(prefix="/species", tags=["species"])


@router.get("", response_model=list[SpeciesResponse])
def list_species(
    db: Session = Depends(get_db),
    active_in_ui: bool | None = Query(default=True),
) -> list[Species]:
    # Authz: public catalog metadata; no auth required.
    stmt = select(Species)
    if active_in_ui is not None:
        stmt = stmt.where(Species.active_in_ui.is_(active_in_ui))
    return list(db.scalars(stmt.order_by(Species.name)).all())
