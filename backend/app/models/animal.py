import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Animal(Base):
    __tablename__ = "animals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    species_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("species.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    photo_urls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner = relationship("User", back_populates="animals")
    species = relationship("Species", back_populates="animals")
    listings = relationship("Listing", back_populates="animal")
