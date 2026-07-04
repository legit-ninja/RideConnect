import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db_types import JSON_DICT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PlatformFlagType(str, enum.Enum):
    INVITE_REDEMPTION_RATE = "invite_redemption_rate"
    MINOR_INVITE_SKEW = "minor_invite_skew"
    OFF_PLATFORM_CONTACT = "off_platform_contact"


class PlatformFlag(Base):
    __tablename__ = "platform_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    flag_type: Mapped[PlatformFlagType] = mapped_column(
        Enum(
            PlatformFlagType,
            name="platform_flag_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    details: Mapped[dict | None] = mapped_column(JSON_DICT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User", foreign_keys=[user_id])
