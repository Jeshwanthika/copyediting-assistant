from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Rule
from app.schemas import (
    ExampleCreate,
    ExampleRead,
    ExampleUpdate,
    RuleRead,
    RuleReviewDetail,
    RuleReviewSummary,
    RuleUpdate,
)
from app.services import rule_review_service, rule_service
from app.services.rule_review_service import RuleUpdateError

router = APIRouter(tags=["rules"])


def _rule_or_404(db: Session, rule_id: int) -> Rule:
    rule = rule_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Rule {rule_id} not found")
    return rule


@router.get("/rules", response_model=list[RuleRead])
def list_rules(
    category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return rule_service.list_rules(db, category=category, status=status)


# NOTE: /rules/review must be declared before /rules/{rule_id}.
@router.get("/rules/review", response_model=list[RuleReviewSummary])
def review_all_rules(db: Session = Depends(get_db)):
    """Every rule with its status, completeness and missing fields."""
    return rule_review_service.review_summaries(db)


@router.get("/rules/{rule_id}", response_model=RuleRead)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    return _rule_or_404(db, rule_id)


@router.get("/rules/{rule_id}/review", response_model=RuleReviewDetail)
def review_rule(rule_id: int, db: Session = Depends(get_db)):
    return rule_review_service.review_detail(db, _rule_or_404(db, rule_id))


@router.patch("/rules/{rule_id}", response_model=RuleReviewDetail)
def update_rule(rule_id: int, update: RuleUpdate, db: Session = Depends(get_db)):
    """Change only the allowed fields. Status changes are explicit and validated."""
    rule = _rule_or_404(db, rule_id)
    try:
        rule = rule_review_service.update_rule(db, rule, update)
    except RuleUpdateError as error:
        raise HTTPException(422, str(error)) from error
    return rule_review_service.review_detail(db, rule)


@router.get("/examples/{rule_id}", response_model=list[ExampleRead])
def list_examples(rule_id: int, db: Session = Depends(get_db)):
    _rule_or_404(db, rule_id)
    return rule_service.list_examples(db, rule_id)


@router.post(
    "/rules/{rule_id}/examples", response_model=ExampleRead, status_code=status.HTTP_201_CREATED
)
def create_example(rule_id: int, data: ExampleCreate, db: Session = Depends(get_db)):
    _rule_or_404(db, rule_id)
    return rule_service.create_example(db, rule_id, data)


@router.patch("/rules/{rule_id}/examples/{example_id}", response_model=ExampleRead)
def update_example(rule_id: int, example_id: int, data: ExampleUpdate, db: Session = Depends(get_db)):
    example = rule_service.get_example(db, rule_id, example_id)
    if example is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Example {example_id} not found")
    return rule_service.update_example(db, example, data)


@router.delete("/rules/{rule_id}/examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_example(rule_id: int, example_id: int, db: Session = Depends(get_db)):
    example = rule_service.get_example(db, rule_id, example_id)
    if example is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Example {example_id} not found")
    rule_service.delete_example(db, example)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
