"""Tiny, idempotent schema upgrades for existing SQLite databases.

`create_all` only creates missing tables; it never changes existing ones. When a
model gains a column, this module upgrades databases created by an earlier stage
so nobody has to delete their data. It runs on every startup and does nothing
when the database is already up to date. SQLite only (the MVP database).
"""
from sqlalchemy import Engine, inspect

from app.models import Feedback


def run_migrations(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    _add_rule_condition(engine)
    _upgrade_feedback(engine)


def _columns(engine: Engine, table: str) -> dict[str, dict]:
    return {col["name"]: col for col in inspect(engine).get_columns(table)}


def _add_rule_condition(engine: Engine) -> None:
    """Stage 3: rules.condition."""
    if "condition" in _columns(engine, "rules"):
        return
    with engine.begin() as conn:
        conn.exec_driver_sql('ALTER TABLE rules ADD COLUMN "condition" TEXT')


def _upgrade_feedback(engine: Engine) -> None:
    """Stage 3: feedback.feedback_type, and rating is no longer required.

    SQLite cannot drop a NOT NULL constraint in place, so the table is rebuilt and
    existing rows are copied across. A row that already has a lead correction
    becomes a lead_correction; everything else becomes trainee_feedback.
    """
    columns = _columns(engine, "feedback")
    if "feedback_type" in columns and columns["rating"]["nullable"]:
        return
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP INDEX IF EXISTS ix_feedback_question_id")
        conn.exec_driver_sql("ALTER TABLE feedback RENAME TO feedback_old")
        Feedback.__table__.create(conn)
        conn.exec_driver_sql(
            """
            INSERT INTO feedback
                (id, question_id, feedback_type, rating, trainee_comment, lead_correction, created_at)
            SELECT id, question_id,
                   CASE WHEN lead_correction IS NOT NULL AND TRIM(lead_correction) <> ''
                        THEN 'lead_correction' ELSE 'trainee_feedback' END,
                   rating, trainee_comment, lead_correction,
                   COALESCE(created_at, CURRENT_TIMESTAMP)
            FROM feedback_old
            """
        )
        conn.exec_driver_sql("DROP TABLE feedback_old")
