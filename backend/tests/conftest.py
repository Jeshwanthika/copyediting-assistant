import json
import os
import tempfile
from pathlib import Path

# Must be set before the app is imported so tests never touch the real database.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, SessionLocal, get_db, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Rule  # noqa: E402
from app.services.seed_service import seed_examples, seed_rules  # noqa: E402


@pytest.fixture(scope="session")
def client():
    init_db()
    with SessionLocal() as db:
        seed_rules(db)
        seed_examples(db)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def fresh_client():
    """A client with its own private, freshly seeded database.

    Use this for tests that change rules, so they cannot affect other tests.
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine, expire_on_commit=False)
    with make_session() as db:
        seed_rules(db)
        seed_examples(db)

    def override_get_db():
        db = make_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
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
