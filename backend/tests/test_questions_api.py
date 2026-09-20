"""API tests for POST /questions (matching, no match, ambiguity, persistence)."""
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Question


def ask(client, text: str) -> dict:
    response = client.post("/questions", json={"question_text": text})
    assert response.status_code == 201, response.text
    return response.json()


def test_matching_question_returns_structured_answer(client):
    body = ask(client, "Can I change the order of authors?")

    assert body["question_id"] == body["id"]
    assert body["question_text"] == "Can I change the order of authors?"
    assert body["matched_rule"]["rule_code"] == "AUTHOR-009"
    assert body["matched_rule"]["topic"] == "Author order"

    answer = body["answer"]
    assert answer["matched"] is True and answer["match_status"] == "matched"
    assert answer["decision"] == "Do not change the author order without author approval."
    assert answer["action"].startswith("Keep the supplied author order.")
    assert answer["source"] == "Initial team guidance"
    assert answer["status"] == "draft"
    assert "not yet been confirmed" in answer["status_notice"]
    assert 0.5 <= answer["confidence"] <= 0.95
    assert answer["escalation_required"] is True
    assert answer["candidates"] == []


def test_matched_rule_and_category_are_saved(client):
    body = ask(client, "What is a snippet?")

    with SessionLocal() as db:
        saved = db.scalars(select(Question).where(Question.id == body["question_id"])).one()
    assert saved.matched_rule_id == body["matched_rule"]["rule_id"]
    assert saved.category == "Author"


def test_rule_without_escalation_does_not_require_it(client):
    answer = ask(client, "What is a snippet?")["answer"]
    assert answer["escalation_required"] is False
    assert answer["escalation_reason"] is None


def test_non_matching_question_says_no_rule_and_is_still_saved(client):
    body = ask(client, "What is the weather today?")

    assert body["matched_rule"] is None
    assert body["matched_rule_id"] is None
    answer = body["answer"]
    assert answer["matched"] is False and answer["match_status"] == "no_match"
    assert answer["decision"] == "No approved rule matched this question."
    assert answer["action"] == "Please check the style manual or raise the question with a lead."
    assert answer["escalation_required"] is True
    assert answer["escalation_reason"] == "No sufficiently relevant rule was found."
    assert answer["confidence"] == 0.0

    with SessionLocal() as db:
        saved = db.get(Question, body["question_id"])
    assert saved is not None and saved.matched_rule_id is None


def test_ambiguous_question_lists_candidates_and_does_not_guess(client):
    body = ask(client, "Is 'van der' a particle name?")

    assert body["matched_rule"] is None
    answer = body["answer"]
    assert answer["match_status"] == "ambiguous"
    assert answer["decision"].startswith("Multiple rules may apply.")
    assert answer["escalation_required"] is True
    assert {c["rule_code"] for c in answer["candidates"]} == {"AUTHOR-003", "AUTHOR-007"}
    assert all(c["rule_text"] for c in answer["candidates"])


def test_original_question_fields_are_still_returned(client):
    body = ask(client, "How should I tag a nickname?")
    for field in ("id", "question_text", "category", "matched_rule_id", "created_at"):
        assert field in body


def test_saved_questions_are_listed_with_their_matched_rule(client):
    body = ask(client, "Does every author need an email ID?")
    listed = {q["id"]: q for q in client.get("/questions?limit=200").json()}
    assert listed[body["question_id"]]["matched_rule_id"] == body["matched_rule"]["rule_id"]


def test_explicit_category_is_kept(client):
    response = client.post(
        "/questions", json={"question_text": "What is a snippet?", "category": "Custom"}
    )
    assert response.json()["category"] == "Custom"


def test_blank_question_is_still_rejected(client):
    assert client.post("/questions", json={"question_text": "   "}).status_code == 422
