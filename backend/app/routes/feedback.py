from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FeedbackCreate, FeedbackRead
from app.services import question_service

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def create_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    """Save trainee feedback (with a rating) or a lead correction (with the correction text)."""
    if question_service.get_question(db, data.question_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Question {data.question_id} not found")
    return question_service.save_feedback(db, data)


@router.get("/feedback", response_model=list[FeedbackRead])
def list_feedback(
    feedback_type: Literal["trainee_feedback", "lead_correction"] | None = None,
    question_id: int | None = None,
    db: Session = Depends(get_db),
):
    return question_service.list_feedback(db, feedback_type=feedback_type, question_id=question_id)
