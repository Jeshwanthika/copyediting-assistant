"""Login, tokens and who may do what (lead/admin vs trainee vs not signed in)."""
import time

import pytest

from app.models import User
from app.services import auth_service
from tests.conftest import LEAD_LOGIN, TRAINEE_LOGIN

NOBODY = {"Authorization": ""}


def first_rule_id(client) -> int:
    return client.get("/rules").json()[0]["id"]


# ------------------------------------------------------------------ login


def test_login_returns_token_and_role(fresh_client):
    body = fresh_client.post("/auth/login", json=LEAD_LOGIN).json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["role"] == "lead" and body["user"]["is_lead"] is True

    body = fresh_client.post("/auth/login", json=TRAINEE_LOGIN).json()
    assert body["user"]["role"] == "trainee" and body["user"]["is_lead"] is False


def test_login_is_case_insensitive_for_username(fresh_client):
    login = {**LEAD_LOGIN, "username": LEAD_LOGIN["username"].upper()}
    assert fresh_client.post("/auth/login", json=login).status_code == 200


@pytest.mark.parametrize(
    "login",
    [
        {"username": "lead", "password": "wrong-password"},
        {"username": "nobody", "password": "lead-test-pass"},
    ],
)
def test_wrong_login_is_rejected_with_one_message(fresh_client, login):
    response = fresh_client.post("/auth/login", json=login)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."


def test_me(fresh_client, trainee_headers):
    assert fresh_client.get("/auth/me").json()["role"] == "lead"
    assert fresh_client.get("/auth/me", headers=trainee_headers).json()["role"] == "trainee"
    assert fresh_client.get("/auth/me", headers=NOBODY).status_code == 401


def test_tampered_or_expired_token_is_rejected(fresh_client, trainee_headers):
    token = trainee_headers["Authorization"].removeprefix("Bearer ")
    payload, signature = token.split(".")
    # A trainee cannot turn their token into a lead token without the key.
    forged = auth_service._b64(b'{"uid": 2, "role": "lead", "exp": 9999999999}')
    for bad in (f"{forged}.{signature}", f"{payload}.x{signature}", "garbage"):
        response = fresh_client.get("/auth/me", headers={"Authorization": f"Bearer {bad}"})
        assert response.status_code == 401

    with pytest.raises(auth_service.AuthError, match="expired"):
        auth_service.read_token(token, now=time.time() + 400 * 24 * 3600)


def test_password_hashing():
    stored = auth_service.hash_password("correct horse")
    assert "correct horse" not in stored
    assert auth_service.verify_password("correct horse", stored)
    assert not auth_service.verify_password("Correct horse", stored)
    assert not auth_service.verify_password("x", "not-a-hash")


def test_change_password(fresh_client, trainee_headers):
    bad = fresh_client.post(
        "/auth/change-password",
        json={"current_password": "wrong", "new_password": "a-new-password"},
        headers=trainee_headers,
    )
    assert bad.status_code == 422
    ok = fresh_client.post(
        "/auth/change-password",
        json={"current_password": TRAINEE_LOGIN["password"], "new_password": "a-new-password"},
        headers=trainee_headers,
    )
    assert ok.status_code == 204
    assert fresh_client.post("/auth/login", json=TRAINEE_LOGIN).status_code == 401
    new_login = {"username": "trainee", "password": "a-new-password"}
    assert fresh_client.post("/auth/login", json=new_login).status_code == 200


def test_create_user_validation():
    with pytest.raises(ValueError, match="Role"):
        auth_service.create_user(None, "x", "long-enough-pw", "admin")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at least"):
        auth_service.create_user(None, "x", "short", "trainee")  # type: ignore[arg-type]


def test_role_change_invalidates_old_token(fresh_client, trainee_headers):
    from app.database import get_db
    from app.main import app

    db = next(app.dependency_overrides[get_db]())
    user = db.query(User).filter(User.username == "trainee").one()
    user.role = "lead"
    db.commit()
    response = fresh_client.get("/auth/me", headers=trainee_headers)
    assert response.status_code == 401
    assert "sign in again" in response.json()["detail"]


# ------------------------------------------------------------------ access rules


def test_health_is_open(fresh_client):
    assert fresh_client.get("/health", headers=NOBODY).status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/rules"),
        ("get", "/rules/review"),
        ("post", "/questions"),
        ("get", "/documents"),
    ],
)
def test_everything_else_needs_login(fresh_client, method, path):
    kwargs = {"json": {"question_text": "Author order?"}} if method == "post" else {}
    response = getattr(fresh_client, method)(path, headers=NOBODY, **kwargs)
    assert response.status_code == 401


def test_trainee_can_read_rules_and_ask(fresh_client, trainee_headers):
    rule_id = first_rule_id(fresh_client)
    assert fresh_client.get("/rules", headers=trainee_headers).status_code == 200
    assert fresh_client.get(f"/rules/{rule_id}", headers=trainee_headers).status_code == 200
    assert fresh_client.get(f"/examples/{rule_id}", headers=trainee_headers).status_code == 200
    asked = fresh_client.post(
        "/questions", json={"question_text": "Can I change the order of authors?"},
        headers=trainee_headers,
    )
    assert asked.status_code == 201
    rated = fresh_client.post(
        "/feedback", json={"question_id": asked.json()["id"], "rating": 4}, headers=trainee_headers
    )
    assert rated.status_code == 201


def test_trainee_cannot_see_knowledge_base_or_edit(fresh_client, trainee_headers):
    rule_id = first_rule_id(fresh_client)
    forbidden = [
        fresh_client.get("/rules/review", headers=trainee_headers),
        fresh_client.get(f"/rules/{rule_id}/review", headers=trainee_headers),
        fresh_client.patch(f"/rules/{rule_id}", json={"action": "x"}, headers=trainee_headers),
        fresh_client.post(
            f"/rules/{rule_id}/examples",
            json={"input_text": "a", "correct_output": "b"},
            headers=trainee_headers,
        ),
        fresh_client.get("/questions", headers=trainee_headers),
        fresh_client.get("/feedback", headers=trainee_headers),
    ]
    assert [r.status_code for r in forbidden] == [403] * len(forbidden)
    # and the rule really was not changed
    assert fresh_client.get(f"/rules/{rule_id}").json()["action"] is None


def test_trainee_cannot_write_lead_correction(fresh_client, trainee_headers):
    qid = fresh_client.post("/questions", json={"question_text": "Q?"}).json()["id"]
    body = {"question_id": qid, "feedback_type": "lead_correction", "lead_correction": "No."}
    assert fresh_client.post("/feedback", json=body, headers=trainee_headers).status_code == 403
    assert fresh_client.post("/feedback", json=body).status_code == 201  # lead


def test_lead_can_edit(fresh_client):
    rule_id = first_rule_id(fresh_client)
    response = fresh_client.patch(f"/rules/{rule_id}", json={"action": "Do this."})
    assert response.status_code == 200
    assert response.json()["rule"]["action"] == "Do this."


def test_default_users_only_created_once(fresh_client):
    from app.database import get_db
    from app.main import app

    db = next(app.dependency_overrides[get_db]())
    assert auth_service.ensure_default_users(db) == []
    assert db.query(User).count() == 2
