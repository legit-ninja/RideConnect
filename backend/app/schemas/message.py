from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    sender_id: UUID
    body: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int


class CreateMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
