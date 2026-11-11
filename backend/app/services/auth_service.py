"""Passwords, login tokens and user accounts. Standard library only.

Passwords are stored as salted PBKDF2-SHA256 hashes. A login token is a small
signed JSON payload (user id, role, expiry) - the same idea as a JWT, without the
extra dependency. The signature uses settings.resolved_secret_key, so a token
cannot be forged or have its role changed without that key.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ROLE_LEAD, ROLE_TRAINEE, ROLES, User

PBKDF2_ITERATIONS = 240_000
MIN_PASSWORD_LENGTH = 8


class AuthError(Exception):
    """Login failed or a token is not valid. The message is safe to show."""


# ------------------------------------------------------------------ passwords


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


# ------------------------------------------------------------------ tokens


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: str) -> str:
    key = settings.resolved_secret_key.encode("utf-8")
    return _b64(hmac.new(key, payload.encode("ascii"), hashlib.sha256).digest())


def create_token(user: User, now: float | None = None) -> tuple[str, int]:
    """Return (token, expiry as a Unix timestamp)."""
    expires = int((now or time.time()) + settings.auth_token_hours * 3600)
    payload = _b64(json.dumps({"uid": user.id, "role": user.role, "exp": expires}).encode())
    return f"{payload}.{_sign(payload)}", expires


@dataclass(frozen=True)
class TokenData:
    user_id: int
    role: str
    expires: int


def read_token(token: str, now: float | None = None) -> TokenData:
    try:
        payload, signature = token.split(".")
    except ValueError:
        raise AuthError("Invalid login token.") from None
    if not hmac.compare_digest(_sign(payload), signature):
        raise AuthError("Invalid login token.")
    try:
        data = json.loads(_unb64(payload))
        result = TokenData(int(data["uid"]), str(data["role"]), int(data["exp"]))
    except (ValueError, KeyError, TypeError):
        raise AuthError("Invalid login token.") from None
    if result.expires < (now or time.time()):
        raise AuthError("Your session has expired. Please sign in again.")
    return result


# ------------------------------------------------------------------ users


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalars(
        select(User).where(func.lower(User.username) == username.strip().lower())
    ).first()


def authenticate(db: Session, username: str, password: str) -> User:
    """Return the user if the username and password are right, else raise AuthError."""
    user = get_user_by_username(db, username)
    # Same message whether the user or the password is wrong.
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AuthError("Incorrect username or password.")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


def user_from_token(db: Session, token: str) -> User:
    data = read_token(token)
    user = db.get(User, data.user_id)
    if user is None or not user.is_active:
        raise AuthError("This account no longer exists or has been disabled.")
    if user.role != data.role:
        # The role was changed after this token was issued.
        raise AuthError("Your access level has changed. Please sign in again.")
    return user


def create_user(
    db: Session, username: str, password: str, role: str, display_name: str | None = None
) -> User:
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if get_user_by_username(db, username) is not None:
        raise ValueError(f"User '{username}' already exists.")
    user = User(
        username=username,
        display_name=(display_name or username).strip(),
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    return user


def set_password(db: Session, user: User, password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    user.password_hash = hash_password(password)
    db.commit()


def ensure_default_users(db: Session) -> list[str]:
    """Create the default lead and trainee accounts, but only if there are no users at all.

    Returns the usernames created (empty if users already existed).
    """
    if db.scalar(select(func.count()).select_from(User)):
        return []
    created = []
    for username, password, role, name in (
        (settings.default_lead_username, settings.default_lead_password, ROLE_LEAD, "Lead editor"),
        (
            settings.default_trainee_username,
            settings.default_trainee_password,
            ROLE_TRAINEE,
            "Trainee",
        ),
    ):
        if username and password:
            create_user(db, username, password, role, name)
            created.append(username)
    return created
