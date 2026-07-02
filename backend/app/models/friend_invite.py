import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class FriendInviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class FriendInvite(Base):
    __tablename__ = "friend_invites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    rider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    invitee_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[FriendInviteStatus] = mapped_column(
        Enum(
            FriendInviteStatus,
            name="friend_invite_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=FriendInviteStatus.PENDING,
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner = relationship("User", foreign_keys=[owner_id])
    rider = relationship("User", foreign_keys=[rider_id])
