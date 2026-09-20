import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.database import Base
from app.models import Rule
from app.services.seed_service import seed_rules


def _new_db() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def _seed_file(tmp_path, **overrides):
    item = {
        "rule_code": "TEST-001", "category": "Author", "topic": "Test topic",
        "rule_text": "Original text.", "source": "Initial team guidance",
        "status": "draft", "version": 1, **overrides,
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps([item]), encoding="utf-8")
    return path


def test_default_seeding_never_overwrites_existing_rules(tmp_path):
    with _new_db() as db:
        seed_rules(db, _seed_file(tmp_path))
        result = seed_rules(db, _seed_file(tmp_path, rule_text="Changed."))
        assert (result.inserted, result.updated, result.unchanged) == (0, 0, 1)
        assert db.scalars(select(Rule.rule_text)).one() == "Original text."


def test_update_mode_applies_changes_and_bumps_version(tmp_path):
    with _new_db() as db:
        seed_rules(db, _seed_file(tmp_path))
        result = seed_rules(db, _seed_file(tmp_path, action="Do it."), update=True)
        assert result.updated == 1
        rule = db.scalars(select(Rule)).one()
        assert rule.action == "Do it." and rule.version == 2

        again = seed_rules(db, _seed_file(tmp_path, action="Do it."), update=True)
        assert again.updated == 0 and db.scalars(select(Rule)).one().version == 2
