from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    question_id: int
    rating: int = Field(ge=1, le=5)
    trainee_comment: str | None = Field(default=None, max_length=2000)
    lead_correction: str | None = Field(default=None, max_length=2000)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    rating: int
    trainee_comment: str | None
    lead_correction: str | None
    created_at: datetime
