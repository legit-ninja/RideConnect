import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SlotStatus(str, enum.Enum):
    OPEN = "open"
    HELD = "held"
    BOOKED = "booked"
    BLOCKED = "blocked"


class ListingAvailabilitySlot(Base):
    __tablename__ = "listing_availability_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False, index=True
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SlotStatus] = mapped_column(
        Enum(
            SlotStatus,
            name="slot_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=SlotStatus.OPEN,
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    listing = relationship("Listing", back_populates="availability_slots")
