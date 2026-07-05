import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ActivityType(str, enum.Enum):
    LESSON = "lesson"
    LEASE = "lease"
    TRAIL_RIDE = "trail_ride"
    DAY_RENTAL = "day_rental"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    animal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(
            ActivityType,
            name="activity_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    availability: Mapped[str | None] = mapped_column(Text, nullable=True)
    friend_only_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    display_location: Mapped[str] = mapped_column(String(256), nullable=False)
    public_lat: Mapped[float] = mapped_column(Float, nullable=False)
    public_lng: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    animal = relationship("Animal", back_populates="listings")
    owner = relationship("User", back_populates="listings")
    photos = relationship("ListingPhoto", back_populates="listing")
    availability_slots = relationship(
        "ListingAvailabilitySlot", back_populates="listing", cascade="all, delete-orphan"
    )
