"""Database access for editorial rules and their examples."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Example, Rule, RuleStatus
from app.schemas import ExampleCreate, ExampleUpdate


def list_rules(db: Session, category: str | None = None, status: str | None = None) -> list[Rule]:
    query = select(Rule).order_by(Rule.rule_code)
    if category:
        query = query.where(Rule.category == category)
    if status:
        query = query.where(Rule.status == status)
    return list(db.scalars(query))


def list_matchable_rules(db: Session) -> list[Rule]:
    """Rules that may be used to answer questions: everything except superseded."""
    query = select(Rule).where(Rule.status != RuleStatus.SUPERSEDED.value).order_by(Rule.rule_code)
    return list(db.scalars(query))


def get_rule(db: Session, rule_id: int) -> Rule | None:
    return db.get(Rule, rule_id)


def list_examples(db: Session, rule_id: int) -> list[Example]:
    query = select(Example).where(Example.rule_id == rule_id).order_by(Example.id)
    return list(db.scalars(query))


def count_examples_by_rule(db: Session) -> dict[int, int]:
    rows = db.execute(select(Example.rule_id, func.count()).group_by(Example.rule_id))
    return {rule_id: count for rule_id, count in rows}


def create_example(db: Session, rule_id: int, data: ExampleCreate) -> Example:
    example = Example(rule_id=rule_id, **data.model_dump())
    db.add(example)
    db.commit()
    db.refresh(example)
    return example


def get_example(db: Session, rule_id: int, example_id: int) -> Example | None:
    example = db.get(Example, example_id)
    return example if example is not None and example.rule_id == rule_id else None


def update_example(db: Session, example: Example, data: ExampleUpdate) -> Example:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(example, field, value)
    db.commit()
    db.refresh(example)
    return example


def delete_example(db: Session, example: Example) -> None:
    db.delete(example)
    db.commit()
