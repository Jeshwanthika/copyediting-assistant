"""Question handling. For now this only stores the question.

Later stages will add question understanding and rule retrieval here.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feedback, Question
from app.schemas import FeedbackCreate, QuestionCreate


def save_question(db: Session, data: QuestionCreate) -> Question:
    question = Question(question_text=data.question_text, category=data.category)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def list_questions(db: Session, limit: int, offset: int) -> list[Question]:
    query = select(Question).order_by(Question.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(query))


def get_question(db: Session, question_id: int) -> Question | None:
    return db.get(Question, question_id)


def save_feedback(db: Session, data: FeedbackCreate) -> Feedback:
    feedback = Feedback(**data.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
