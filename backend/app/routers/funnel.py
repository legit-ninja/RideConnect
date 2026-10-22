from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user_optional
from app.models.shop import FunnelEvent
from app.models.user import User
from app.schemas.funnel import FunnelEventCreate, FunnelEventResponse

router = APIRouter(prefix="/funnel", tags=["funnel"])


@router.post(
    "/events",
    response_model=FunnelEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_funnel_event(
    payload: FunnelEventCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> FunnelEventResponse:
    # Authz: public ingest (optional auth); no PII beyond optional user_id from token.
    event = FunnelEvent(
        business_unit=payload.business_unit,
        stage=payload.stage.strip(),
        user_id=current_user.id if current_user else None,
        anon_id=payload.anon_id,
        src=payload.src,
        ref=payload.ref,
        path=payload.path,
        payload=payload.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return FunnelEventResponse(id=event.id, ok=True)
