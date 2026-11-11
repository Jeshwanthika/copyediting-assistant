from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, PasswordChange, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Exchange a username and password for a login token."""
    try:
        user = auth_service.authenticate(db, data.username, data.password)
    except auth_service.AuthError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error
    token, expires = auth_service.create_token(user)
    return LoginResponse(
        access_token=token,
        expires_at=datetime.fromtimestamp(expires, tz=timezone.utc),
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    """Who the token belongs to. The frontend calls this to check a saved login."""
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    if not auth_service.verify_password(data.current_password, user.password_hash):
        raise HTTPException(422, "Current password is incorrect.")
    auth_service.set_password(db, user, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
