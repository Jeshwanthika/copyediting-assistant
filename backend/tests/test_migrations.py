"""Upgrading a database that was created by Stage 2."""
import sqlite3

from sqlalchemy import create_engine, inspect

from app.migrations import run_migrations

STAGE2_SCHEMA = """
CREATE TABLE rules (
    id INTEGER PRIMARY KEY, rule_code VARCHAR(50) NOT NULL UNIQUE, category VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL, question_pattern TEXT, rule_text TEXT NOT NULL, action TEXT,
    exception TEXT, escalation TEXT, source VARCHAR(200) NOT NULL, source_section VARCHAR(200),
    status VARCHAR(30) NOT NULL, version INTEGER NOT NULL, created_at DATETIME, updated_at DATETIME
);
CREATE TABLE questions (id INTEGER PRIMARY KEY, question_text TEXT NOT NULL, category VARCHAR(100),
    matched_rule_id INTEGER REFERENCES rules(id), created_at DATETIME);
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL REFERENCES questions(id),
    rating INTEGER NOT NULL, trainee_comment TEXT, lead_correction TEXT, created_at DATETIME
);
CREATE INDEX ix_feedback_question_id ON feedback (question_id);
INSERT INTO rules (id, rule_code, category, topic, rule_text, source, status, version)
    VALUES (1, 'AUTHOR-001', 'Author', 'Multiple given names', 'Text.', 'Initial team guidance', 'draft', 1);
INSERT INTO questions (id, question_text) VALUES (1, 'Q?');
INSERT INTO feedback (question_id, rating, trainee_comment, created_at) VALUES (1, 4, 'ok', '2026-01-01 10:00:00');
INSERT INTO feedback (question_id, rating, lead_correction) VALUES (1, 3, 'Use AUTHOR-002');  -- no created_at
"""


def make_stage2_db(path):
    connection = sqlite3.connect(path)
    connection.executescript(STAGE2_SCHEMA)
    connection.commit()
    connection.close()
    return create_engine(f"sqlite:///{path}")


def test_stage2_database_is_upgraded_without_losing_data(tmp_path):
    engine = make_stage2_db(tmp_path / "old.db")
    run_migrations(engine)

    inspector = inspect(engine)
    assert "condition" in {c["name"] for c in inspector.get_columns("rules")}
    feedback_columns = {c["name"]: c for c in inspector.get_columns("feedback")}
    assert "feedback_type" in feedback_columns
    assert feedback_columns["rating"]["nullable"] is True

    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT rule_code, condition FROM rules").all() == [("AUTHOR-001", None)]
        rows = conn.exec_driver_sql(
            "SELECT feedback_type, rating, trainee_comment, lead_correction FROM feedback ORDER BY id"
        ).all()
    assert rows == [
        ("trainee_feedback", 4, "ok", None),
        ("lead_correction", 3, None, "Use AUTHOR-002"),  # already had a lead correction
    ]


def test_migrations_can_run_twice(tmp_path):
    engine = make_stage2_db(tmp_path / "old.db")
    run_migrations(engine)
    run_migrations(engine)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT COUNT(*) FROM feedback").scalar() == 2


def test_upgraded_feedback_table_accepts_a_lead_correction_without_rating(tmp_path):
    engine = make_stage2_db(tmp_path / "old.db")
    run_migrations(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO feedback (question_id, feedback_type, lead_correction, created_at) "
            "VALUES (1, 'lead_correction', 'x', '2026-01-02')"
        )
