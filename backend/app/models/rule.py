from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    topic: Mapped[str] = mapped_column(String(200))
    question_pattern: Mapped[str | None] = mapped_column(Text, default=None)
    # When the rule applies (e.g. "Only for corresponding authors"). Optional.
    condition: Mapped[str | None] = mapped_column(Text, default=None)
    rule_text: Mapped[str] = mapped_column(Text)
    action: Mapped[str | None] = mapped_column(Text, default=None)
    exception: Mapped[str | None] = mapped_column(Text, default=None)
    escalation: Mapped[str | None] = mapped_column(Text, default=None)
    source: Mapped[str] = mapped_column(String(200))
    source_section: Mapped[str | None] = mapped_column(String(200), default=None)
    # draft / reviewed / confirmed / superseded (see models/rule_status.py)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    examples = relationship("Example", back_populates="rule", cascade="all, delete-orphan")
