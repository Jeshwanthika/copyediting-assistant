def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_rules_are_seeded_as_draft(client):
    rules = client.get("/rules").json()
    assert len(rules) == 20
    assert all(r["status"] == "draft" for r in rules)
    assert all(r["source"] == "Initial team guidance" for r in rules)
    assert rules[0]["rule_code"] == "AUTHOR-001"


def test_get_rule_and_404(client):
    rule_id = client.get("/rules").json()[0]["id"]
    assert client.get(f"/rules/{rule_id}").status_code == 200
    assert client.get("/rules/9999").status_code == 404


def test_create_and_list_question(client):
    response = client.post("/questions", json={"question_text": "How do I tag a nickname?"})
    assert response.status_code == 201
    # Stage 2: the question is matched to a rule (AUTHOR-008, nicknames) and saved with it.
    assert response.json()["matched_rule"]["rule_code"] == "AUTHOR-008"
    assert any(q["id"] == response.json()["id"] for q in client.get("/questions").json())


def test_blank_question_rejected(client):
    assert client.post("/questions", json={"question_text": "  "}).status_code == 422


def test_feedback_flow(client):
    qid = client.post("/questions", json={"question_text": "Q?"}).json()["id"]
    ok = client.post("/feedback", json={"question_id": qid, "rating": 5})
    assert ok.status_code == 201
    assert client.post("/feedback", json={"question_id": 9999, "rating": 5}).status_code == 404
    assert client.post("/feedback", json={"question_id": qid, "rating": 6}).status_code == 422


def test_examples_endpoint(client):
    rule_id = client.get("/rules").json()[0]["id"]
    assert client.get(f"/examples/{rule_id}").json() == []
    assert client.get("/examples/9999").status_code == 404
