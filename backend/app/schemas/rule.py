from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_code: str
    category: str
    topic: str
    question_pattern: str | None
    condition: str | None
    rule_text: str
    action: str | None
    exception: str | None
    escalation: str | None
    source: str
    source_section: str | None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


class RuleUpdate(BaseModel):
    """The only fields PATCH /rules/{id} accepts.

    Anything else (rule_code, topic, id, timestamps, ...) is rejected with a 422
    because of extra="forbid". Fields left out are not changed. Sending an empty
    string for an optional field clears it.
    """

    model_config = ConfigDict(extra="forbid")

    condition: str | None = Field(default=None, max_length=5000)
    rule_text: str | None = Field(default=None, max_length=5000)
    action: str | None = Field(default=None, max_length=5000)
    exception: str | None = Field(default=None, max_length=5000)
    escalation: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=200)
    source_section: str | None = Field(default=None, max_length=200)
    status: Literal["draft", "reviewed", "confirmed", "superseded"] | None = None
    version: int | None = Field(default=None, ge=1)

    @field_validator("rule_text", "source", "status", "version", mode="before")
    @classmethod
    def cannot_be_cleared(cls, value):
        """These fields may be changed but never removed."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError("this field cannot be empty")
        return value
