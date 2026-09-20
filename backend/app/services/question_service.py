"""Question handling: match a question to a rule, build the answer, save the question.

Flow: route -> question_service -> rule_engine (matching) + answer_builder -> database.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feedback, Question, Rule
from app.schemas import FeedbackCreate, MatchedRule, QuestionAnswerResponse, QuestionCreate
from app.services import answer_builder, rule_engine, rule_service


def answer_question(db: Session, data: QuestionCreate) -> QuestionAnswerResponse:
    """Find the matching rule, save the question with the match, and return the answer."""
    rules = rule_service.list_matchable_rules(db)  # superseded rules are never used
    result = rule_engine.match_question(data.question_text, rules)
    rule = result.best.rule if result.best else None

    question = save_question(
        db,
        data,
        matched_rule_id=rule.id if rule else None,
        category=data.category or (rule.category if rule else None),
    )
    examples = rule_service.list_examples(db, rule.id) if rule else []
    return QuestionAnswerResponse(
        **_question_fields(question),
        question_id=question.id,
        matched_rule=_matched_rule(rule),
        answer=answer_builder.build_answer(result, examples),
    )


def _question_fields(question: Question) -> dict:
    return {
        "id": question.id,
        "question_text": question.question_text,
        "category": question.category,
        "matched_rule_id": question.matched_rule_id,
        "created_at": question.created_at,
    }


def _matched_rule(rule: Rule | None) -> MatchedRule | None:
    if rule is None:
        return None
    return MatchedRule(rule_id=rule.id, rule_code=rule.rule_code, topic=rule.topic, version=rule.version)


def save_question(
    db: Session,
    data: QuestionCreate,
    matched_rule_id: int | None = None,
    category: str | None = None,
) -> Question:
    question = Question(
        question_text=data.question_text,
        category=category if category is not None else data.category,
        matched_rule_id=matched_rule_id,
    )
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


def list_feedback(
    db: Session, feedback_type: str | None = None, question_id: int | None = None
) -> list[Feedback]:
    query = select(Feedback).order_by(Feedback.id.desc())
    if feedback_type:
        query = query.where(Feedback.feedback_type == feedback_type)
    if question_id is not None:
        query = query.where(Feedback.question_id == question_id)
    return list(db.scalars(query))
