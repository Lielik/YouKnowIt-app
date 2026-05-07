# FastAPI dependencies — injected into routes that need authentication
# get_current_user: raises 401 if not logged in (use on protected routes)
# get_optional_user: returns None if not logged in (use on public routes)

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User


def get_current_user(
    access_token: Optional[str] = Cookie(
        default=None),  # reads token from browser cookie
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    if not access_token:
        raise credentials_exception

    # Verify token signature and expiry
    payload = decode_access_token(access_token)
    if payload is None:
        raise credentials_exception

    # "sub" is the standard JWT field we use to store the user ID
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Make sure the user still exists in the DB
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_optional_user(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not access_token:
        return None
    try:
        return get_current_user(access_token=access_token, db=db)
    except HTTPException:
        return None
