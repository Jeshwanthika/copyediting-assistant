"""Turn a rule-engine result into the structured answer shown to the trainee.

Everything here comes from the matched rule's stored fields. Nothing is invented.
If the matched rule is incomplete (see rule_completeness.py) the answer says so and
sends the trainee to the style manual or a lead; a missing action is never filled in.
"""
from typing import Sequence

from app.models import Example, status_notice
from app.schemas import Answer, AnswerExample, CandidateRule
from app.services.rule_completeness import check_completeness
from app.services.rule_engine import Candidate, MatchResult, MatchStatus

NO_MATCH_DECISION = "No approved rule matched this question."
NO_MATCH_ACTION = "Please check the style manual or raise the question with a lead."
NO_MATCH_REASON = "No sufficiently relevant rule was found."

AMBIGUOUS_DECISION = (
    "Multiple rules may apply. Please review the relevant guidance or raise a query with a lead."
)
AMBIGUOUS_ACTION = "Review the possible rules below, or raise a query with a lead."
AMBIGUOUS_ESCALATION = "Multiple rules may apply and the system cannot choose between them."

INCOMPLETE_NOTICE = "Guidance found, but this rule is incomplete."
INCOMPLETE_ACTION = "Check the style manual or raise the question with a lead."


def build_answer(result: MatchResult, examples: Sequence[Example] = ()) -> Answer:
    """`examples` are the matched rule's examples (empty if it has none)."""
    if result.status == MatchStatus.MATCHED and result.best is not None:
        return _matched_answer(result.best, result.confidence, examples)
    if result.status == MatchStatus.AMBIGUOUS:
        return _ambiguous_answer(result.candidates)
    return _no_match_answer()


def _matched_answer(candidate: Candidate, confidence: float, examples: Sequence[Example]) -> Answer:
    rule = candidate.rule
    completeness = check_completeness(rule, len(examples))
    terms = ", ".join(f"\u201c{t}\u201d" for t in candidate.matched_terms)

    if completeness.complete:
        action = rule.action
        escalation_required = bool(rule.escalation and rule.escalation.strip())
        escalation_reason = (
            f"The matched rule requires a query/lead confirmation: {rule.escalation}"
            if escalation_required
            else None
        )
        incomplete_notice = None
    else:
        # Never fill the gap: show what is recorded, and send the trainee onwards.
        action = INCOMPLETE_ACTION
        escalation_required = True
        escalation_reason = (
            f"This rule is incomplete (missing: {', '.join(completeness.missing_fields)}), "
            "so it cannot be applied without checking."
        )
        if rule.escalation and rule.escalation.strip():
            escalation_reason += f" The rule itself also says: {rule.escalation}"
        incomplete_notice = INCOMPLETE_NOTICE

    return Answer(
        matched=True,
        match_status="matched",
        decision=rule.rule_text,
        action=action,
        reason=(
            f"Your question matches rule {rule.rule_code} ({rule.topic}) "
            f"on the words: {terms}."
        ),
        rule_code=rule.rule_code,
        rule_topic=rule.topic,
        source=rule.source,
        status=rule.status,
        status_notice=status_notice(rule.status),
        rule_complete=completeness.complete,
        missing_fields=completeness.missing_fields,
        incomplete_notice=incomplete_notice,
        condition=rule.condition,
        exception=rule.exception,
        examples=[
            AnswerExample(
                input_text=e.input_text,
                correct_output=e.correct_output,
                explanation=e.explanation,
            )
            for e in examples
        ],
        confidence=confidence,
        matched_terms=list(candidate.matched_terms),
        escalation_required=escalation_required,
        escalation_reason=escalation_reason,
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
        rule_complete=None,
        missing_fields=[],
        incomplete_notice=None,
        condition=None,
        exception=None,
        examples=[],
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
        rule_complete=None,
        missing_fields=[],
        incomplete_notice=None,
        condition=None,
        exception=None,
        examples=[],
        confidence=0.0,
        matched_terms=[],
        escalation_required=True,
        escalation_reason=NO_MATCH_REASON,
        candidates=[],
    )
