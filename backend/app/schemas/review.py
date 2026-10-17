from pydantic import BaseModel

from app.schemas.example import ExampleRead
from app.schemas.rule import RuleRead


class RuleCompleteness(BaseModel):
    rule_code: str
    complete: bool
    # Required information that is missing: rule_text, action, source, status
    missing_fields: list[str]
    # Optional information, reported but never required
    has_condition: bool
    has_exception: bool
    has_escalation: bool
    has_source_section: bool
    has_example: bool
    example_count: int


class RuleReviewSummary(BaseModel):
    rule_id: int
    rule_code: str
    topic: str
    category: str
    status: str
    version: int
    complete: bool
    missing_fields: list[str]
    has_exception: bool
    has_escalation: bool
    has_example: bool


class RuleReviewDetail(BaseModel):
    rule: RuleRead
    completeness: RuleCompleteness
    examples: list[ExampleRead]
    allowed_status_transitions: list[str]
    # What a trainee is told about this rule's status
    status_notice: str
