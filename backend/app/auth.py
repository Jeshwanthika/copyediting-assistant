"""FastAPI dependencies that enforce login and roles.

    current_user  - any signed-in user (lead or trainee)
    require_lead  - only leads/admins; trainees get 403

Every route except /health and /auth/login uses one of these. The frontend also
hides lead-only pages, but these checks are what actually protect the data.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services import auth_service

_bearer = HTTPBearer(auto_error=False, description="Token from POST /auth/login")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return auth_service.user_from_token(db, credentials.credentials)
    except auth_service.AuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, str(error), headers={"WWW-Authenticate": "Bearer"}
        ) from error


def require_lead(user: User = Depends(current_user)) -> User:
    if not user.is_lead:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only leads and admins can do this.")
    return user
