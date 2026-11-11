from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionCreate(BaseModel):
    question_text: str = Field(max_length=2000)
    category: str | None = Field(default=None, max_length=100)

    @field_validator("question_text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question_text must not be empty")
        return value


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_text: str
    category: str | None
    matched_rule_id: int | None
    created_at: datetime
