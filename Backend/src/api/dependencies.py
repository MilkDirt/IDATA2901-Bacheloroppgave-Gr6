"""
Shared FastAPI dependencies for the RAG API.

This module provides reusable dependency functions that can be
injected into any FastAPI endpoint using FastAPI's Depends() system.

"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from src.db.database import get_db
from src.db.models import User
from src.api.auth import SECRET_KEY, ALGORITHM

# OAuth2PasswordBearer tells FastAPI to look for a Bearer token
# in the Authorization header of incoming requests.
# The tokenUrl points to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
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
        token (str): JWT token extracted from the Authorization header.
        db (Session): Database session injected by FastAPI.

    Returns:
        User: The authenticated user object from the database.

    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the user ID stored in the token
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