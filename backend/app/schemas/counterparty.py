from uuid import UUID

from pydantic import BaseModel, Field


class CounterpartyProfile(BaseModel):
    id: UUID
    first_name: str
    last_initial: str
    self_reported_skill_label: str | None = None
    confirmed_skill_label: str | None = None
    is_horse_trainer: bool = False
    is_riding_instructor: bool = False
    trainer_verified: bool = False
    trainer_self_report_labels: list[str] = Field(default_factory=list)
