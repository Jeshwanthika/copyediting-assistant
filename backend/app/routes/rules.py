from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ExampleRead, RuleRead
from app.services import rule_service

router = APIRouter(tags=["rules"])


@router.get("/rules", response_model=list[RuleRead])
def list_rules(
    category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return rule_service.list_rules(db, category=category, status=status)


@router.get("/rules/{rule_id}", response_model=RuleRead)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Rule {rule_id} not found")
    return rule


@router.get("/examples/{rule_id}", response_model=list[ExampleRead])
def list_examples(rule_id: int, db: Session = Depends(get_db)):
    if rule_service.get_rule(db, rule_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Rule {rule_id} not found")
    return rule_service.list_examples(db, rule_id)
