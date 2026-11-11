from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: int
    input_text: str
    correct_output: str
    explanation: str | None
    created_at: datetime


def _not_blank(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("this field cannot be empty")
    return value


class ExampleCreate(BaseModel):
    input_text: str = Field(max_length=2000)
    correct_output: str = Field(max_length=2000)
    explanation: str | None = Field(default=None, max_length=2000)

    @field_validator("input_text", "correct_output")
    @classmethod
    def required_text(cls, value: str) -> str:
        return _not_blank(value)  # type: ignore[return-value]

    @field_validator("explanation")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class ExampleUpdate(BaseModel):
    """Fields left out are not changed."""

    model_config = ConfigDict(extra="forbid")

    input_text: str | None = Field(default=None, max_length=2000)
    correct_output: str | None = Field(default=None, max_length=2000)
    explanation: str | None = Field(default=None, max_length=2000)

    @field_validator("input_text", "correct_output", mode="before")
    @classmethod
    def cannot_be_cleared(cls, value):
        if value is None:
            raise ValueError("this field cannot be empty")
        return value

    @field_validator("input_text", "correct_output")
    @classmethod
    def required_text(cls, value: str | None) -> str | None:
        return _not_blank(value)

    @field_validator("explanation")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None
