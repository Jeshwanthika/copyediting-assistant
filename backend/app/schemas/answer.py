from typing import Literal

from pydantic import BaseModel

from app.schemas.question import QuestionRead


class MatchedRule(BaseModel):
    rule_id: int
    rule_code: str
    topic: str
    version: int


class CandidateRule(BaseModel):
    """A rule that could apply when the system cannot choose between several."""

    rule_code: str
    topic: str
    rule_text: str


class Answer(BaseModel):
    matched: bool
    match_status: Literal["matched", "no_match", "ambiguous"]
    decision: str
    action: str
    reason: str
    rule_code: str | None
    rule_topic: str | None
    source: str | None
    status: str | None
    # Shown whenever the rule is not yet confirmed against the official style manual.
    status_notice: str | None
    exception: str | None
    confidence: float  # 0.0 to 1.0 keyword-match strength; 0.0 when nothing matched
    matched_terms: list[str]
    escalation_required: bool
    escalation_reason: str | None
    candidates: list[CandidateRule]


class QuestionAnswerResponse(QuestionRead):
    """Response of POST /questions.

    Extends QuestionRead, so the original fields (id, question_text, category,
    matched_rule_id, created_at) are still present for existing clients.
    """

    question_id: int
    matched_rule: MatchedRule | None
    answer: Answer
