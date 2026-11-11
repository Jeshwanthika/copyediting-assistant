import json
import os
import tempfile
from pathlib import Path

# Must be set before the app is imported so tests never touch the real database.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["DOCUMENTS_DIR"] = tempfile.mkdtemp(prefix="ce-docs-")
os.environ["AUTH_SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["DEFAULT_LEAD_USERNAME"] = "lead"
os.environ["DEFAULT_LEAD_PASSWORD"] = "lead-test-pass"
os.environ["DEFAULT_TRAINEE_USERNAME"] = "trainee"
os.environ["DEFAULT_TRAINEE_PASSWORD"] = "trainee-test-pass"

LEAD_LOGIN = {"username": "lead", "password": "lead-test-pass"}
TRAINEE_LOGIN = {"username": "trainee", "password": "trainee-test-pass"}

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, SessionLocal, get_db, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Rule  # noqa: E402
from app.services.auth_service import ensure_default_users  # noqa: E402
from app.services.seed_service import seed_examples, seed_rules  # noqa: E402


def auth_headers(test_client: TestClient, login: dict) -> dict[str, str]:
    response = test_client.post("/auth/login", json=login)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def lead_headers(fresh_client) -> dict[str, str]:
    return auth_headers(fresh_client, LEAD_LOGIN)


@pytest.fixture()
def trainee_headers(fresh_client) -> dict[str, str]:
    return auth_headers(fresh_client, TRAINEE_LOGIN)


@pytest.fixture(scope="session")
def client():
    """Shared client, signed in as a lead (so existing tests can use every endpoint)."""
    init_db()
    with SessionLocal() as db:
        seed_rules(db)
        seed_examples(db)
        ensure_default_users(db)
    with TestClient(app) as test_client:
        test_client.headers.update(auth_headers(test_client, LEAD_LOGIN))
        yield test_client


@pytest.fixture()
def fresh_client():
    """A client with its own private, freshly seeded database.

    Use this for tests that change rules, so they cannot affect other tests.
    Signed in as a lead by default; pass `headers=trainee_headers` (or
    `headers={"Authorization": ""}` for nobody) on a request to act as someone else.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine, expire_on_commit=False)
    with make_session() as db:
        seed_rules(db)
        seed_examples(db)
        ensure_default_users(db)

    def override_get_db():
        db = make_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.headers.update(auth_headers(test_client, LEAD_LOGIN))
        yield test_client
    app.dependency_overrides.clear()


SEED_FILE = Path(__file__).resolve().parents[2] / "data" / "seed" / "rules.json"


@pytest.fixture(scope="session")
def seed_items() -> dict[str, dict]:
    """The seed rules as plain dicts, keyed by rule_code (the expected values in tests)."""
    return {item["rule_code"]: item for item in json.loads(SEED_FILE.read_text("utf-8"))}


@pytest.fixture(scope="session")
def rules(seed_items) -> list[Rule]:
    """Rule objects built straight from the seed file. No database needed."""
    return [Rule(id=i, **item) for i, item in enumerate(seed_items.values(), start=1)]


@pytest.fixture(scope="session")
def complete_rules(seed_items) -> list[Rule]:
    """Test data only: the seed rules with a placeholder action filled in.

    Lets the matching/escalation tests check behaviour for COMPLETE rules. The real
    seed rules (mostly without an action) are used to test incomplete-rule behaviour.
    """
    return [
        Rule(id=i, **{**item, "action": item["action"] or f"Test action for {item['rule_code']}"})
        for i, item in enumerate(seed_items.values(), start=1)
    ]
