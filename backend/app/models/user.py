from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.rule import utcnow

# Leads (and admins) maintain rules, the knowledge base and the errors & solutions PDFs.
ROLE_LEAD = "lead"
# Trainees (and other staff) can read rules and PDFs and ask questions. Nothing else.
ROLE_TRAINEE = "trainee"
ROLES = (ROLE_LEAD, ROLE_TRAINEE)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    # "pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>" - never the plain password.
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=ROLE_TRAINEE, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    @property
    def is_lead(self) -> bool:
        return self.role == ROLE_LEAD
