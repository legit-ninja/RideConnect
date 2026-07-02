import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_rider: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(
            VerificationStatus,
            name="verification_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
    )
    is_minor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guardian_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    guardian = relationship("User", remote_side=[id], foreign_keys=[guardian_user_id])
    oauth_accounts = relationship("OAuthAccount", back_populates="user")
    animals = relationship("Animal", back_populates="owner")
    listings = relationship("Listing", back_populates="owner")
