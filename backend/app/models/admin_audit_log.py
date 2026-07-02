import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AdminAuditAction(str, enum.Enum):
    VERIFICATION_STATUS_CHANGED = "verification_status_changed"
    USER_ROLES_CHANGED = "user_roles_changed"
    LISTING_DEACTIVATED = "listing_deactivated"
    LISTING_REACTIVATED = "listing_reactivated"


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[AdminAuditAction] = mapped_column(
        Enum(
            AdminAuditAction,
            name="admin_audit_action",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    actor = relationship("User", foreign_keys=[actor_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
