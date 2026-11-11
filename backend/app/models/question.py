from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.rule import utcnow


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), default=None)
    # Filled in later, once rule retrieval exists.
    matched_rule_id: Mapped[int | None] = mapped_column(ForeignKey("rules.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
