from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    created_at: datetime

    model_config = {"from_attributes": True}
