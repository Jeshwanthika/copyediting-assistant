"""Decide whether a rule has enough information to be used to answer a trainee.

A rule is COMPLETE when all of these are filled in (and status is a known status):
    rule_text, action, source, status

Reported but NOT required (some rules legitimately have none of these):
    condition, exception, escalation, source_section, examples

Works on any object with the rule's fields, so it can also check the values a
rule WOULD have after an update, before anything is saved.
"""
from typing import Any

from app.models import VALID_STATUSES
from app.schemas import RuleCompleteness

REQUIRED_FIELDS = ("rule_text", "action", "source", "status")


def _blank(value: Any) -> bool:
    return value is None or not str(value).strip()


def check_completeness(rule: Any, example_count: int = 0) -> RuleCompleteness:
    missing = [name for name in REQUIRED_FIELDS if _blank(getattr(rule, name, None))]
    if "status" not in missing and rule.status not in VALID_STATUSES:
        missing.append("status")
    return RuleCompleteness(
        rule_code=rule.rule_code,
        complete=not missing,
        missing_fields=missing,
        has_condition=not _blank(getattr(rule, "condition", None)),
        has_exception=not _blank(getattr(rule, "exception", None)),
        has_escalation=not _blank(getattr(rule, "escalation", None)),
        has_source_section=not _blank(getattr(rule, "source_section", None)),
        has_example=example_count > 0,
        example_count=example_count,
    )
