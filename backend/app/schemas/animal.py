from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.riding_style import RidingStyle


class AnimalCreateRequest(BaseModel):
    species_id: UUID
    name: str = Field(min_length=1, max_length=128)
    breed: str | None = Field(default=None, max_length=128)
    age: int | None = Field(default=None, ge=0, le=100)
    description: str | None = Field(default=None, max_length=5000)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: str = Field(min_length=1, max_length=512)
    photo_urls: list[str] = Field(default_factory=list)
    riding_styles: list[RidingStyle] = Field(default_factory=list)

    @field_validator("riding_styles")
    @classmethod
    def unique_riding_styles(cls, values: list[RidingStyle]) -> list[RidingStyle]:
        seen: set[RidingStyle] = set()
        unique: list[RidingStyle] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique.append(value)
        return unique


class AnimalUpdateRequest(BaseModel):
    species_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    breed: str | None = Field(default=None, max_length=128)
    age: int | None = Field(default=None, ge=0, le=100)
    description: str | None = Field(default=None, max_length=5000)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, min_length=1, max_length=512)
    photo_urls: list[str] | None = None
    riding_styles: list[RidingStyle] | None = None

    @field_validator("riding_styles")
    @classmethod
    def unique_riding_styles(
        cls, values: list[RidingStyle] | None
    ) -> list[RidingStyle] | None:
        if values is None:
            return None
        seen: set[RidingStyle] = set()
        unique: list[RidingStyle] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique.append(value)
        return unique


class AnimalResponse(BaseModel):
    id: UUID
    owner_id: UUID
    species_id: UUID
    name: str
    breed: str | None
    age: int | None
    description: str | None
    lat: float
    lng: float
    address: str
    photo_urls: list[str]
    riding_styles: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
