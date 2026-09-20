from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.rule import utcnow

TRAINEE_FEEDBACK = "trainee_feedback"
LEAD_CORRECTION = "lead_correction"
FEEDBACK_TYPES = (TRAINEE_FEEDBACK, LEAD_CORRECTION)


class Feedback(Base):
    """A reaction to an answered question.

    feedback_type says who it is from:
      trainee_feedback  a rating (and optional comment) from a trainee
      lead_correction   a correction written by a lead (no rating)
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    feedback_type: Mapped[str] = mapped_column(String(30), default=TRAINEE_FEEDBACK, index=True)
    rating: Mapped[int | None] = mapped_column(Integer, default=None)  # 1 (poor) to 5 (excellent)
    trainee_comment: Mapped[str | None] = mapped_column(Text, default=None)
    lead_correction: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
