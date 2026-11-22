"""
API Dependencies
Provides database session and JWT authentication with user-scoping.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates JWT Bearer token and returns authenticated User.
    Accepts Bearer header or ?token= query parameter (for direct file downloads/views).
    Raises 401 if missing, invalid, or expired.
    """
    raw_token = auth.credentials if (auth and auth.credentials) else token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(raw_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
