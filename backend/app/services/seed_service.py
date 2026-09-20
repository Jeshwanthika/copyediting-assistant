"""Load seed data from data/seed/*.json into the database."""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import SEED_DIR
from app.models import Rule


def seed_rules(db: Session, seed_file: Path = SEED_DIR / "rules.json") -> tuple[int, int]:
    """Insert rules that do not exist yet (matched by rule_code).

    Returns (inserted, skipped). Existing rules are never overwritten, so edits
    made in the database are safe.
    """
    rules = json.loads(seed_file.read_text(encoding="utf-8"))
    existing = set(db.scalars(select(Rule.rule_code)))
    inserted = 0
    for item in rules:
        if item["rule_code"] in existing:
            continue
        db.add(Rule(**item))
        inserted += 1
    db.commit()
    return inserted, len(rules) - inserted
