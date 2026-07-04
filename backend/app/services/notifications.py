import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    kind: str,
    body: str,
    payload: dict | None = None,
) -> Notification:
    notification = Notification(user_id=user_id, kind=kind, body=body, payload=payload)
    db.add(notification)
    db.flush()
    return notification
