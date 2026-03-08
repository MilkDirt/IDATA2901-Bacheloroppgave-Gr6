"""
Shared FastAPI dependencies for the RAG API.

This module provides reusable dependency functions that can be
injected into any FastAPI endpoint using FastAPI's Depends() system.

Currently provides:
- get_current_user: Extracts and validates the JWT token from the
  request header and returns the authenticated user from the database.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from src.db.database import get_db
from src.db.models import User
from src.api.auth import SECRET_KEY, ALGORITHM

# HTTPBearer tells FastAPI to look for a Bearer token
# in the Authorization header of incoming requests.
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that validates the JWT token and returns the current user.

    This function is injected into protected endpoints using Depends().
    It will automatically reject requests that:
    - Have no Authorization header
    - Have an invalid or expired token
    - Reference a user that no longer exists in the database

    Args:
        credentials: HTTP Bearer credentials from the Authorization header.
        db (Session): Database session injected by FastAPI.

    Returns:
        User: The authenticated user object from the database.

    Raises:
        HTTPException 401: If the token is missing, invalid, or expired.
        HTTPException 404: If the user in the token no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract the raw token string from the credentials
        token = credentials.credentials

        # Decode the JWT token using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the user ID stored in the token ("sub" = subject)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        # Token is invalid or has expired
        raise credentials_exception

    # Look up the user in the database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user