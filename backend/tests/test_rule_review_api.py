"""Rule review endpoints, controlled updates, status transitions and examples.

These use `fresh_client` (a private database per test) because they change rules.
"""
import pytest

DRAFT_TEXT = "Draft team guidance \u2014 not yet confirmed against the official style manual."


def rid(client, code: str) -> int:
    return next(r["id"] for r in client.get("/rules").json() if r["rule_code"] == code)


def get_rule(client, code: str) -> dict:
    return client.get(f"/rules/{rid(client, code)}").json()


def patch(client, code: str, **fields):
    return client.patch(f"/rules/{rid(client, code)}", json=fields)


def ask(client, text: str) -> dict:
    return client.post("/questions", json={"question_text": text}).json()["answer"]


# ------------------------------------------------------------------ review


def test_review_list_reports_status_and_completeness(fresh_client):
    response = fresh_client.get("/rules/review")
    assert response.status_code == 200
    items = {i["rule_code"]: i for i in response.json()}

    assert len(items) == 20
    assert {i["status"] for i in items.values()} == {"draft"}  # nothing is pre-approved
    assert items["AUTHOR-009"]["complete"] is True and items["AUTHOR-009"]["missing_fields"] == []
    assert items["AUTHOR-001"]["complete"] is False
    assert items["AUTHOR-001"]["missing_fields"] == ["action"]
    assert sum(i["complete"] for i in items.values()) == 1
    assert items["AUTHOR-009"]["has_example"] is True
    assert items["AUTHOR-001"]["has_example"] is False
    assert items["AUTHOR-004"]["has_escalation"] is True
    assert items["AUTHOR-011"]["has_escalation"] is False
    for key in ("rule_id", "topic", "version", "has_exception"):
        assert key in items["AUTHOR-001"]


def test_review_list_is_not_confused_with_rule_id_route(fresh_client):
    assert fresh_client.get("/rules/review").status_code == 200
    assert fresh_client.get("/rules/9999").status_code == 404


def test_review_detail_for_one_rule(fresh_client):
    body = fresh_client.get(f"/rules/{rid(fresh_client, 'AUTHOR-001')}/review").json()
    assert body["rule"]["rule_code"] == "AUTHOR-001"
    assert body["completeness"]["complete"] is False
    assert body["completeness"]["missing_fields"] == ["action"]
    assert body["examples"] == []
    assert body["allowed_status_transitions"] == ["reviewed", "superseded"]
    assert body["status_notice"] == DRAFT_TEXT
    assert fresh_client.get("/rules/9999/review").status_code == 404


def test_review_detail_includes_examples(fresh_client):
    body = fresh_client.get(f"/rules/{rid(fresh_client, 'AUTHOR-009')}/review").json()
    assert body["completeness"]["has_example"] is True
    assert body["examples"][0]["input_text"] == "Can I reorder the authors?"
    assert body["examples"][0]["correct_output"] == (
        "Do not change the author order without author approval."
    )


# ------------------------------------------------------------------- PATCH


def test_patch_updates_allowed_fields(fresh_client):
    response = patch(
        fresh_client, "AUTHOR-001",
        condition="Author has several given names", action="Tag every part except the last as given name.",
        exception="None known", escalation="Raise a query if unclear", source="Style manual",
        source_section="3.2", version=4,
    )
    assert response.status_code == 200
    rule = response.json()["rule"]
    assert rule["action"] == "Tag every part except the last as given name."
    assert rule["condition"] == "Author has several given names"
    assert rule["exception"] == "None known" and rule["escalation"] == "Raise a query if unclear"
    assert rule["source"] == "Style manual" and rule["source_section"] == "3.2"
    assert rule["version"] == 4  # an explicit version is respected
    assert response.json()["completeness"]["complete"] is True
    assert get_rule(fresh_client, "AUTHOR-001")["action"] == rule["action"]  # really saved


def test_patch_leaves_omitted_fields_alone(fresh_client):
    before = get_rule(fresh_client, "AUTHOR-002")
    patch(fresh_client, "AUTHOR-002", action="New action")
    after = get_rule(fresh_client, "AUTHOR-002")
    for field in ("rule_text", "escalation", "source", "topic", "rule_code", "status"):
        assert after[field] == before[field]
    assert after["action"] == "New action"


@pytest.mark.parametrize(
    "field, value",
    [
        ("rule_code", "HACK-001"), ("topic", "New topic"), ("id", 99), ("category", "X"),
        ("created_at", "2020-01-01T00:00:00"), ("updated_at", "2020-01-01T00:00:00"),
        ("question_pattern", "x"), ("not_a_field", 1),
    ],
)
def test_patch_rejects_fields_that_are_not_allowed(fresh_client, field, value):
    before = get_rule(fresh_client, "AUTHOR-003")
    response = patch(fresh_client, "AUTHOR-003", **{field: value})
    assert response.status_code == 422
    assert get_rule(fresh_client, "AUTHOR-003") == before  # nothing changed


def test_patch_cannot_blank_required_fields(fresh_client):
    for field in ("rule_text", "source"):
        assert patch(fresh_client, "AUTHOR-003", **{field: "  "}).status_code == 422
        assert patch(fresh_client, "AUTHOR-003", **{field: None}).status_code == 422


def test_patch_can_clear_optional_fields_with_empty_text(fresh_client):
    patch(fresh_client, "AUTHOR-004", exception="Temporary")
    patch(fresh_client, "AUTHOR-004", exception="", escalation="  ")
    rule = get_rule(fresh_client, "AUTHOR-004")
    assert rule["exception"] is None and rule["escalation"] is None


def test_patch_validates_values(fresh_client):
    assert patch(fresh_client, "AUTHOR-003", status="approved").status_code == 422
    assert patch(fresh_client, "AUTHOR-003", version=0).status_code == 422
    assert patch(fresh_client, "AUTHOR-003", version="abc").status_code == 422
    assert fresh_client.patch("/rules/9999", json={"action": "x"}).status_code == 404


def test_content_edit_bumps_version_unless_one_is_given(fresh_client):
    assert get_rule(fresh_client, "AUTHOR-005")["version"] == 1
    patch(fresh_client, "AUTHOR-005", action="A")
    assert get_rule(fresh_client, "AUTHOR-005")["version"] == 2
    patch(fresh_client, "AUTHOR-005", source_section="1.1")  # not a content field
    assert get_rule(fresh_client, "AUTHOR-005")["version"] == 2


def test_empty_patch_changes_nothing(fresh_client):
    before = get_rule(fresh_client, "AUTHOR-005")
    assert patch(fresh_client, "AUTHOR-005").status_code == 200
    assert get_rule(fresh_client, "AUTHOR-005") == before


# ----------------------------------------------------------- status changes


def test_lead_can_move_draft_to_reviewed_to_confirmed(fresh_client):
    assert get_rule(fresh_client, "AUTHOR-009")["status"] == "draft"

    assert patch(fresh_client, "AUTHOR-009", status="reviewed").json()["rule"]["status"] == "reviewed"
    response = patch(fresh_client, "AUTHOR-009", status="confirmed")
    assert response.status_code == 200
    assert response.json()["rule"]["status"] == "confirmed"
    assert response.json()["status_notice"] == "Confirmed guidance."
    assert response.json()["allowed_status_transitions"] == ["draft", "superseded"]


def test_draft_cannot_jump_straight_to_confirmed(fresh_client):
    response = patch(fresh_client, "AUTHOR-009", status="confirmed")
    assert response.status_code == 422
    assert "draft rule cannot change to confirmed" in response.json()["detail"]
    assert get_rule(fresh_client, "AUTHOR-009")["status"] == "draft"


def test_incomplete_rule_cannot_be_confirmed(fresh_client):
    assert patch(fresh_client, "AUTHOR-001", status="reviewed").status_code == 200
    response = patch(fresh_client, "AUTHOR-001", status="confirmed")
    assert response.status_code == 422
    assert "incomplete" in response.json()["detail"] and "action" in response.json()["detail"]
    assert get_rule(fresh_client, "AUTHOR-001")["status"] == "reviewed"

    # Adding the missing action and confirming in one request works.
    ok = patch(fresh_client, "AUTHOR-001", action="Do X", status="confirmed")
    assert ok.status_code == 200 and ok.json()["rule"]["status"] == "confirmed"


def test_other_transitions(fresh_client):
    patch(fresh_client, "AUTHOR-009", status="reviewed")
    assert patch(fresh_client, "AUTHOR-009", status="draft").json()["rule"]["status"] == "draft"
    patch(fresh_client, "AUTHOR-009", status="reviewed")
    patch(fresh_client, "AUTHOR-009", status="confirmed")
    assert patch(fresh_client, "AUTHOR-009", status="draft").status_code == 200  # reopen
    assert patch(fresh_client, "AUTHOR-009", status="superseded").status_code == 200
    # superseded is final
    assert patch(fresh_client, "AUTHOR-009", status="draft").status_code == 422


def test_seed_and_reads_never_promote_a_rule(fresh_client):
    fresh_client.get("/rules/review")
    ask(fresh_client, "Can I change the author order?")
    ask(fresh_client, "What is a snippet?")
    assert {r["status"] for r in fresh_client.get("/rules").json()} == {"draft"}


def test_editing_a_confirmed_rule_sends_it_back_to_draft(fresh_client):
    patch(fresh_client, "AUTHOR-009", status="reviewed")
    patch(fresh_client, "AUTHOR-009", status="confirmed")
    assert ask(fresh_client, "Can I change the author order?")["status_notice"] == "Confirmed guidance."

    # The edit form always sends the current status along; that is not a promotion or a decision.
    response = patch(fresh_client, "AUTHOR-009", action="Changed action", status="confirmed")
    assert response.json()["rule"]["status"] == "draft"
    assert ask(fresh_client, "Can I change the author order?")["status_notice"] == DRAFT_TEXT


def test_editing_a_reviewed_rule_sends_it_back_to_draft(fresh_client):
    patch(fresh_client, "AUTHOR-009", status="reviewed")
    response = patch(fresh_client, "AUTHOR-009", rule_text="Changed rule text.")
    assert response.json()["rule"]["status"] == "draft"


def test_non_content_edit_keeps_the_status(fresh_client):
    patch(fresh_client, "AUTHOR-009", status="reviewed")
    assert patch(fresh_client, "AUTHOR-009", source_section="2.1").json()["rule"]["status"] == "reviewed"


def test_confirmed_only_shows_to_trainees_after_an_explicit_update(fresh_client):
    question = "Can I change the author order?"
    assert ask(fresh_client, question)["status"] == "draft"
    patch(fresh_client, "AUTHOR-009", status="reviewed")
    reviewed = ask(fresh_client, question)
    assert reviewed["status"] == "reviewed" and reviewed["status_notice"] != "Confirmed guidance."
    patch(fresh_client, "AUTHOR-009", status="confirmed")
    assert ask(fresh_client, question)["status_notice"] == "Confirmed guidance."


def test_superseded_rules_are_not_used_to_answer(fresh_client):
    patch(fresh_client, "AUTHOR-009", status="superseded")
    answer = ask(fresh_client, "Can I change the author order?")
    assert answer["match_status"] == "no_match"


# ------------------------------------------------ incomplete -> complete flow


def test_completing_a_rule_changes_the_trainee_answer_but_not_its_status(fresh_client):
    question = "What is a snippet?"
    before = ask(fresh_client, question)
    assert before["rule_complete"] is False
    assert before["incomplete_notice"] == "Guidance found, but this rule is incomplete."
    assert before["action"] == "Check the style manual or raise the question with a lead."

    patch(fresh_client, "AUTHOR-011", action="Use the snippet as supplied.")
    after = ask(fresh_client, question)
    assert after["rule_complete"] is True and after["incomplete_notice"] is None
    assert after["action"] == "Use the snippet as supplied."
    assert after["status"] == "draft" and after["status_notice"] == DRAFT_TEXT  # still draft


# ------------------------------------------------------------------ examples


def test_answer_shows_the_example_for_authors_order_only(fresh_client):
    with_example = ask(fresh_client, "Can I change the author order?")
    assert [e["input_text"] for e in with_example["examples"]] == ["Can I reorder the authors?"]
    assert ask(fresh_client, "What is a snippet?")["examples"] == []


def test_only_authors_009_has_a_seed_example(fresh_client):
    codes = {
        r["rule_code"] for r in fresh_client.get("/rules").json()
        if fresh_client.get(f"/examples/{r['id']}").json()
    }
    assert codes == {"AUTHOR-009"}


def test_rule_can_have_several_examples(fresh_client):
    rule_id = rid(fresh_client, "AUTHOR-009")
    created = fresh_client.post(
        f"/rules/{rule_id}/examples",
        json={"input_text": "  Swap authors 1 and 2?  ", "correct_output": "Ask for author approval first."},
    )
    assert created.status_code == 201
    assert created.json()["input_text"] == "Swap authors 1 and 2?"
    assert created.json()["explanation"] is None
    assert len(fresh_client.get(f"/examples/{rule_id}").json()) == 2
    assert len(ask(fresh_client, "Can I change the author order?")["examples"]) == 2


def test_example_validation_and_404s(fresh_client):
    rule_id = rid(fresh_client, "AUTHOR-001")
    assert fresh_client.post(f"/rules/{rule_id}/examples", json={"input_text": " ", "correct_output": "x"}).status_code == 422
    assert fresh_client.post(f"/rules/{rule_id}/examples", json={"input_text": "x"}).status_code == 422
    assert fresh_client.post("/rules/9999/examples", json={"input_text": "x", "correct_output": "y"}).status_code == 404
    assert fresh_client.patch(f"/rules/{rule_id}/examples/9999", json={"input_text": "x"}).status_code == 404
    assert fresh_client.delete(f"/rules/{rule_id}/examples/9999").status_code == 404


def test_example_update_and_delete(fresh_client):
    rule_id = rid(fresh_client, "AUTHOR-009")
    example = fresh_client.get(f"/examples/{rule_id}").json()[0]
    url = f"/rules/{rule_id}/examples/{example['id']}"

    updated = fresh_client.patch(url, json={"explanation": "New explanation"})
    assert updated.status_code == 200 and updated.json()["explanation"] == "New explanation"
    assert updated.json()["input_text"] == example["input_text"]
    assert fresh_client.patch(url, json={"rule_id": 3}).status_code == 422  # cannot move it

    # An example only belongs to its own rule.
    other = rid(fresh_client, "AUTHOR-001")
    assert fresh_client.delete(f"/rules/{other}/examples/{example['id']}").status_code == 404

    assert fresh_client.delete(url).status_code == 204
    assert fresh_client.get(f"/examples/{rule_id}").json() == []
    assert ask(fresh_client, "Can I change the author order?")["examples"] == []


# ------------------------------------------------------------------ feedback


def _question_id(client) -> int:
    return client.post("/questions", json={"question_text": "What is a snippet?"}).json()["question_id"]


def test_trainee_feedback_and_lead_correction_are_kept_apart(fresh_client):
    qid = _question_id(fresh_client)
    trainee = fresh_client.post("/feedback", json={"question_id": qid, "rating": 2, "trainee_comment": "Unclear"})
    lead = fresh_client.post(
        "/feedback",
        json={"question_id": qid, "feedback_type": "lead_correction", "lead_correction": "AUTHOR-001 applies."},
    )
    assert trainee.status_code == 201 and lead.status_code == 201
    assert trainee.json()["feedback_type"] == "trainee_feedback" and trainee.json()["rating"] == 2
    assert lead.json()["feedback_type"] == "lead_correction" and lead.json()["rating"] is None

    only_leads = fresh_client.get("/feedback?feedback_type=lead_correction").json()
    assert [f["id"] for f in only_leads] == [lead.json()["id"]]
    assert len(fresh_client.get(f"/feedback?question_id={qid}").json()) == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"feedback_type": "trainee_feedback"},  # rating missing
        {"feedback_type": "trainee_feedback", "rating": 3, "lead_correction": "x"},
        {"feedback_type": "lead_correction"},  # correction text missing
        {"feedback_type": "lead_correction", "lead_correction": "  "},
        {"feedback_type": "lead_correction", "lead_correction": "x", "rating": 3},
        {"feedback_type": "lead_correction", "lead_correction": "x", "trainee_comment": "y"},
        {"feedback_type": "other", "rating": 3},
    ],
)
def test_feedback_type_rules_are_enforced(fresh_client, payload):
    qid = _question_id(fresh_client)
    assert fresh_client.post("/feedback", json={"question_id": qid, **payload}).status_code == 422
