from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_code: str
    category: str
    topic: str
    question_pattern: str | None
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
