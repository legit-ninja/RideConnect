from uuid import UUID

from pydantic import BaseModel, Field


class SpeciesResponse(BaseModel):
    id: UUID
    name: str
    active_in_ui: bool

    model_config = {"from_attributes": True}
