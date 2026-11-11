"""Vercel entry point for the API.

Vercel's disk is temporary, so the SQLite database lives in /tmp and is created and
seeded on every cold start. Edits, questions and uploaded PDFs do not survive a restart.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402,F401
from app.services.auth_service import ensure_default_users  # noqa: E402
from app.services.seed_service import seed_examples, seed_rules  # noqa: E402

init_db()
with SessionLocal() as db:
    seed_rules(db)
    seed_examples(db)
    ensure_default_users(db)
