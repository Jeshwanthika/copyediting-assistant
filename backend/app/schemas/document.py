from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    original_filename: str
    size_bytes: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class DocumentUpdate(BaseModel):
    """Change a document's details. Fields left out are not changed."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    sort_order: int | None = None
