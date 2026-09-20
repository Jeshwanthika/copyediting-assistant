"""Load seed data from data/seed/*.json into the database."""
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import SEED_DIR
from app.models import Example, Rule

# Fields that the seed file controls when running with update=True.
SEED_FIELDS = (
    "category", "topic", "question_pattern", "condition", "rule_text", "action",
    "exception", "escalation", "source", "source_section", "status",
)


@dataclass(frozen=True)
class SeedResult:
    inserted: int
    updated: int
    unchanged: int


def seed_rules(
    db: Session, seed_file: Path = SEED_DIR / "rules.json", update: bool = False
) -> SeedResult:
    """Insert rules that do not exist yet (matched by rule_code).

    By default existing rules are left alone, so edits made in the database are
    safe. With update=True, existing rules are brought in line with the seed file
    and their `version` is increased if anything changed.
    """
    items = json.loads(seed_file.read_text(encoding="utf-8"))
    existing = {rule.rule_code: rule for rule in db.scalars(select(Rule))}
    inserted = updated = unchanged = 0
    for item in items:
        rule = existing.get(item["rule_code"])
        if rule is None:
            db.add(Rule(**item))
            inserted += 1
        elif update and _apply_changes(rule, item):
            updated += 1
        else:
            unchanged += 1
    db.commit()
    return SeedResult(inserted, updated, unchanged)


def _apply_changes(rule: Rule, item: dict) -> bool:
    changed = False
    for field in SEED_FIELDS:
        if field in item and getattr(rule, field) != item[field]:
            setattr(rule, field, item[field])
            changed = True
    if changed:
        rule.version += 1
    return changed


def seed_examples(db: Session, seed_file: Path = SEED_DIR / "examples.json") -> int:
    """Insert seed examples that do not exist yet (same rule + same input text).

    Only examples written by the team are listed in the file. Returns how many were added.
    """
    items = json.loads(seed_file.read_text(encoding="utf-8"))
    rules = {rule.rule_code: rule for rule in db.scalars(select(Rule))}
    added = 0
    for item in items:
        rule = rules.get(item["rule_code"])
        if rule is None:
            continue
        exists = db.scalars(
            select(Example).where(
                Example.rule_id == rule.id, Example.input_text == item["input_text"]
            )
        ).first()
        if exists:
            continue
        db.add(
            Example(
                rule_id=rule.id,
                input_text=item["input_text"],
                correct_output=item["correct_output"],
                explanation=item.get("explanation"),
            )
        )
        added += 1
    db.commit()
    return added
