"""Turn a rule-engine result into the structured answer shown to the trainee.

Everything here comes from the matched rule's stored fields. Nothing is invented:
where a rule has no `action` stored, a generic instruction is used instead.
"""
from app.schemas import Answer, CandidateRule
from app.services.rule_engine import Candidate, MatchResult, MatchStatus

NO_MATCH_DECISION = "No approved rule matched this question."
NO_MATCH_ACTION = "Please check the style manual or raise the question with a lead."
NO_MATCH_REASON = "No sufficiently relevant rule was found."

AMBIGUOUS_DECISION = (
    "Multiple rules may apply. Please review the relevant guidance or raise a query with a lead."
)
AMBIGUOUS_ACTION = "Review the possible rules below, or raise a query with a lead."
AMBIGUOUS_ESCALATION = "Multiple rules may apply and the system cannot choose between them."

DEFAULT_ACTION = (
    "Apply this rule as written. If your case does not clearly fit it, "
    "check the style manual or raise a query with a lead."
)

DRAFT_NOTICE = (
    "This is draft internal team guidance. It has not yet been confirmed "
    "against the official style manual."
)


def build_answer(result: MatchResult) -> Answer:
    if result.status == MatchStatus.MATCHED and result.best is not None:
        return _matched_answer(result.best, result.confidence)
    if result.status == MatchStatus.AMBIGUOUS:
        return _ambiguous_answer(result.candidates)
    return _no_match_answer()


def _status_notice(status: str) -> str | None:
    """Anything that is not explicitly approved is flagged to the trainee."""
    return None if status == "approved" else DRAFT_NOTICE


def _matched_answer(candidate: Candidate, confidence: float) -> Answer:
    rule = candidate.rule
    needs_query = bool(rule.escalation and rule.escalation.strip())
    terms = ", ".join(f"\u201c{t}\u201d" for t in candidate.matched_terms)
    return Answer(
        matched=True,
        match_status="matched",
        decision=rule.rule_text,
        action=rule.action or DEFAULT_ACTION,
        reason=(
            f"Your question matches rule {rule.rule_code} ({rule.topic}) "
            f"on the words: {terms}."
        ),
        rule_code=rule.rule_code,
        rule_topic=rule.topic,
        source=rule.source,
        status=rule.status,
        status_notice=_status_notice(rule.status),
        exception=rule.exception,
        confidence=confidence,
        matched_terms=list(candidate.matched_terms),
        escalation_required=needs_query,
        escalation_reason=(
            f"The matched rule requires a query/lead confirmation: {rule.escalation}"
            if needs_query
            else None
        ),
        candidates=[],
    )


def _ambiguous_answer(candidates: tuple[Candidate, ...]) -> Answer:
    codes = ", ".join(c.rule.rule_code for c in candidates)
    return Answer(
        matched=False,
        match_status="ambiguous",
        decision=AMBIGUOUS_DECISION,
        action=AMBIGUOUS_ACTION,
        reason=f"Your question matches more than one rule about equally well: {codes}.",
        rule_code=None,
        rule_topic=None,
        source=None,
        status=None,
        status_notice=None,
        exception=None,
        confidence=0.0,
        matched_terms=[],
        escalation_required=True,
        escalation_reason=AMBIGUOUS_ESCALATION,
        candidates=[
            CandidateRule(rule_code=c.rule.rule_code, topic=c.rule.topic, rule_text=c.rule.rule_text)
            for c in candidates
        ],
    )


def _no_match_answer() -> Answer:
    return Answer(
        matched=False,
        match_status="no_match",
        decision=NO_MATCH_DECISION,
        action=NO_MATCH_ACTION,
        reason=NO_MATCH_REASON,
        rule_code=None,
        rule_topic=None,
        source=None,
        status=None,
        status_notice=None,
        exception=None,
        confidence=0.0,
        matched_terms=[],
        escalation_required=True,
        escalation_reason=NO_MATCH_REASON,
        candidates=[],
    )
