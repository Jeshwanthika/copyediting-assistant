import json
import os
import tempfile
from pathlib import Path

# Must be set before the app is imported so tests never touch the real database.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Rule  # noqa: E402
from app.services.seed_service import seed_rules  # noqa: E402


@pytest.fixture(scope="session")
def client():
    init_db()
    with SessionLocal() as db:
        seed_rules(db)
    with TestClient(app) as test_client:
        yield test_client


SEED_FILE = Path(__file__).resolve().parents[2] / "data" / "seed" / "rules.json"


@pytest.fixture(scope="session")
def seed_items() -> dict[str, dict]:
    """The seed rules as plain dicts, keyed by rule_code (the expected values in tests)."""
    return {item["rule_code"]: item for item in json.loads(SEED_FILE.read_text("utf-8"))}


@pytest.fixture(scope="session")
def rules(seed_items) -> list[Rule]:
    """Rule objects built straight from the seed file. No database needed."""
    return [Rule(id=i, **item) for i, item in enumerate(seed_items.values(), start=1)]
