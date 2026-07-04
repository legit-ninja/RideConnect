from pydantic import BaseModel, Field


class CreateEventRequest(BaseModel):
    event_type: str = Field(max_length=64)
    src: str | None = Field(default=None, max_length=64)
    listing_slug: str | None = Field(default=None, max_length=128)
    invite_token: str | None = Field(default=None, max_length=64)
    payload: dict | None = None
