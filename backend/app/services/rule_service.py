"""Database access for editorial rules and their examples."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Example, Rule


def list_rules(db: Session, category: str | None = None, status: str | None = None) -> list[Rule]:
    query = select(Rule).order_by(Rule.rule_code)
    if category:
        query = query.where(Rule.category == category)
    if status:
        query = query.where(Rule.status == status)
    return list(db.scalars(query))


def get_rule(db: Session, rule_id: int) -> Rule | None:
    return db.get(Rule, rule_id)


def list_examples(db: Session, rule_id: int) -> list[Example]:
    query = select(Example).where(Example.rule_id == rule_id).order_by(Example.id)
    return list(db.scalars(query))
