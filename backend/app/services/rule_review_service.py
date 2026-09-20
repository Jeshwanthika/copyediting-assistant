"""Lead/editor review of rules: completeness reports and controlled updates.

The update rules that keep guidance safe:
- Only the fields in RuleUpdate can change (enforced by the schema).
- A status change must follow ALLOWED_TRANSITIONS (draft -> reviewed -> confirmed).
  Nothing ever changes status by itself.
- A rule can only become `confirmed` when it is complete.
- Editing the content of a reviewed/confirmed rule WITHOUT explicitly changing its
  status sends it back to `draft`, because the review no longer applies to what it says.
- If the content changed and no version was supplied, the version goes up by one.
"""
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.models import ALLOWED_TRANSITIONS, Rule, RuleStatus, status_notice
from app.schemas import (
    ExampleRead,
    RuleCompleteness,
    RuleReviewDetail,
    RuleReviewSummary,
    RuleRead,
    RuleUpdate,
)
from app.services import rule_service
from app.services.rule_completeness import check_completeness

CONTENT_FIELDS = ("condition", "rule_text", "action", "exception", "escalation")
OPTIONAL_TEXT_FIELDS = ("condition", "action", "exception", "escalation", "source_section")
_NEEDS_REVIEW_AGAIN = (RuleStatus.REVIEWED.value, RuleStatus.CONFIRMED.value)


class RuleUpdateError(Exception):
    """The requested change is not allowed. The message is safe to show to a lead."""


def review_summaries(db: Session) -> list[RuleReviewSummary]:
    counts = rule_service.count_examples_by_rule(db)
    summaries = []
    for rule in rule_service.list_rules(db):
        report = check_completeness(rule, counts.get(rule.id, 0))
        summaries.append(
            RuleReviewSummary(
                rule_id=rule.id,
                rule_code=rule.rule_code,
                topic=rule.topic,
                category=rule.category,
                status=rule.status,
                version=rule.version,
                complete=report.complete,
                missing_fields=report.missing_fields,
                has_exception=report.has_exception,
                has_escalation=report.has_escalation,
                has_example=report.has_example,
            )
        )
    return summaries


def review_detail(db: Session, rule: Rule) -> RuleReviewDetail:
    examples = rule_service.list_examples(db, rule.id)
    return RuleReviewDetail(
        rule=RuleRead.model_validate(rule),
        completeness=check_completeness(rule, len(examples)),
        examples=[ExampleRead.model_validate(e) for e in examples],
        allowed_status_transitions=list(ALLOWED_TRANSITIONS.get(rule.status, ())),
        status_notice=status_notice(rule.status),
    )


def update_rule(db: Session, rule: Rule, update: RuleUpdate) -> Rule:
    changes = _clean(update.model_dump(exclude_unset=True))
    old_status = rule.status
    requested_status = changes.get("status", old_status)
    explicit_transition = requested_status != old_status
    content_changed = any(
        f in changes and changes[f] != getattr(rule, f) for f in CONTENT_FIELDS
    )

    if explicit_transition and requested_status not in ALLOWED_TRANSITIONS.get(old_status, ()):
        allowed = ", ".join(ALLOWED_TRANSITIONS.get(old_status, ())) or "none"
        raise RuleUpdateError(
            f"A {old_status} rule cannot change to {requested_status}. Allowed: {allowed}."
        )

    new_status = requested_status
    if content_changed and not explicit_transition and old_status in _NEEDS_REVIEW_AGAIN:
        new_status = RuleStatus.DRAFT.value  # the earlier review no longer applies

    result = _resulting_values(rule, changes, new_status)
    if explicit_transition and new_status == RuleStatus.CONFIRMED.value:
        report = check_completeness(result)
        if not report.complete:
            raise RuleUpdateError(
                "An incomplete rule cannot be confirmed. Missing: "
                + ", ".join(report.missing_fields)
                + "."
            )

    for field, value in changes.items():
        if field != "status":
            setattr(rule, field, value)
    rule.status = new_status
    if content_changed and "version" not in changes:
        rule.version += 1
    db.commit()
    db.refresh(rule)
    return rule


def _clean(changes: dict) -> dict:
    """Trim text; an empty optional field means "clear it"."""
    cleaned = {}
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
            if field in OPTIONAL_TEXT_FIELDS and not value:
                value = None
        cleaned[field] = value
    return cleaned


def _resulting_values(rule: Rule, changes: dict, new_status: str) -> SimpleNamespace:
    """What the rule will look like after the update (used to check completeness first)."""
    fields = ("rule_code", "condition", "rule_text", "action", "exception", "escalation",
              "source", "source_section")
    values = {f: changes.get(f, getattr(rule, f)) for f in fields}
    return SimpleNamespace(**values, status=new_status)
