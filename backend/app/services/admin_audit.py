from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.admin_audit_log import AdminAuditAction, AdminAuditLog
from app.models.user import User


def log_admin_action(
    db: Session,
    actor: User,
    action: AdminAuditAction,
    target_user_id: UUID | None,
    metadata: dict[str, Any],
) -> AdminAuditLog:
    entry = AdminAuditLog(
        actor_id=actor.id,
        action=action,
        target_user_id=target_user_id,
        metadata_=metadata,
    )
    db.add(entry)
    return entry


def list_audit_logs(
    db: Session,
    *,
    actor_id: UUID | None,
    target_user_id: UUID | None,
    action: AdminAuditAction | None,
    created_after: datetime | None,
    created_before: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[AdminAuditLog], int]:
    base = select(AdminAuditLog).options(
        selectinload(AdminAuditLog.actor),
        selectinload(AdminAuditLog.target_user),
    )
    count_stmt = select(func.count()).select_from(AdminAuditLog)

    if actor_id is not None:
        base = base.where(AdminAuditLog.actor_id == actor_id)
        count_stmt = count_stmt.where(AdminAuditLog.actor_id == actor_id)

    if target_user_id is not None:
        base = base.where(AdminAuditLog.target_user_id == target_user_id)
        count_stmt = count_stmt.where(AdminAuditLog.target_user_id == target_user_id)

    if action is not None:
        base = base.where(AdminAuditLog.action == action)
        count_stmt = count_stmt.where(AdminAuditLog.action == action)

    if created_after is not None:
        base = base.where(AdminAuditLog.created_at >= created_after)
        count_stmt = count_stmt.where(AdminAuditLog.created_at >= created_after)

    if created_before is not None:
        base = base.where(AdminAuditLog.created_at <= created_before)
        count_stmt = count_stmt.where(AdminAuditLog.created_at <= created_before)

    total = db.scalar(count_stmt) or 0
    entries = list(
        db.scalars(
            base.order_by(AdminAuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return entries, total
