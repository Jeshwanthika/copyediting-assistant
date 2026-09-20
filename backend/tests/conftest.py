import os
import tempfile

# Must be set before the app is imported so tests never touch the real database.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.seed_service import seed_rules  # noqa: E402


@pytest.fixture(scope="session")
def client():
    init_db()
    with SessionLocal() as db:
        seed_rules(db)
    with TestClient(app) as test_client:
        yield test_client
