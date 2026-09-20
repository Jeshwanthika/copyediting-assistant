from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import QuestionAnswerResponse, QuestionCreate, QuestionRead
from app.services import question_service

router = APIRouter(tags=["questions"])


@router.post(
    "/questions", response_model=QuestionAnswerResponse, status_code=status.HTTP_201_CREATED
)
def create_question(data: QuestionCreate, db: Session = Depends(get_db)):
    """Match the question to a rule, save it, and return the structured answer."""
    return question_service.answer_question(db, data)


@router.get("/questions", response_model=list[QuestionRead])
def list_questions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return question_service.list_questions(db, limit=limit, offset=offset)
