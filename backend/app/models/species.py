import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Species(Base):
    __tablename__ = "species"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    active_in_ui: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    animals = relationship("Animal", back_populates="species")
