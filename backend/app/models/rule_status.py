"""Rule statuses and the allowed changes between them.

draft       Initial team guidance. Not checked by a lead yet.
reviewed    A lead has checked the content, but it is not yet confirmed
            against the official style manual.
confirmed   A lead has explicitly confirmed it against the official style manual.
superseded  Replaced by newer guidance. Never used to answer questions.

Nothing in the code ever promotes a rule automatically. Every status change is
requested explicitly (PATCH /rules/{id}) and checked against ALLOWED_TRANSITIONS.
"""
from enum import Enum


class RuleStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    CONFIRMED = "confirmed"
    SUPERSEDED = "superseded"


ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    RuleStatus.DRAFT.value: (RuleStatus.REVIEWED.value, RuleStatus.SUPERSEDED.value),
    RuleStatus.REVIEWED.value: (
        RuleStatus.CONFIRMED.value,
        RuleStatus.DRAFT.value,
        RuleStatus.SUPERSEDED.value,
    ),
    RuleStatus.CONFIRMED.value: (RuleStatus.DRAFT.value, RuleStatus.SUPERSEDED.value),
    RuleStatus.SUPERSEDED.value: (),
}

VALID_STATUSES = tuple(s.value for s in RuleStatus)

# What a trainee is told about a rule, by status.
STATUS_NOTICES: dict[str, str] = {
    RuleStatus.DRAFT.value: (
        "Draft team guidance \u2014 not yet confirmed against the official style manual."
    ),
    RuleStatus.REVIEWED.value: (
        "Reviewed team guidance \u2014 checked by a lead, but not yet confirmed "
        "against the official style manual."
    ),
    RuleStatus.CONFIRMED.value: "Confirmed guidance.",
    RuleStatus.SUPERSEDED.value: "Superseded guidance \u2014 do not rely on it.",
}
UNKNOWN_STATUS_NOTICE = (
    "Status unknown \u2014 treat as draft team guidance, not confirmed against the "
    "official style manual."
)


def status_notice(status: str) -> str:
    """Anything that is not explicitly known is treated as unconfirmed."""
    return STATUS_NOTICES.get(status, UNKNOWN_STATUS_NOTICE)
