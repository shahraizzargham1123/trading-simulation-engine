from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from app.core.config import settings
from app.core.database import get_db
from app.models import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Single-user demo: always returns the seeded demo user.
    Routes still pull `user_id` off this object so the API surface is
    multi-user ready when auth is added later."""
    user = db.query(User).filter(User.username == settings.demo_user_username).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="demo user has not been seeded",
        )
    return user
