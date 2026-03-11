"""
Authentication endpoints for the RAG API.

This module handles:
- User registration with validation
- User login with JWT token generation
- Password hashing and verification
- Email and password validation rules
"""

import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

from src.db.database import get_db
from src.db.models import User

# ── Security config ───────────────────────────────────────
SECRET_KEY = "change-this-to-a-random-string-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 timer

# ── Password hashing ──────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain, hashed)


# ── JWT token ─────────────────────────────────────────────
def create_token(user_id: int) -> str:
    """
    Create a JWT token for the given user ID.

    Args:
        user_id (int): The user's database ID.

    Returns:
        str: Signed JWT token valid for 24 hours.
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


# ── Validation helpers ────────────────────────────────────
def validate_password(password: str) -> str | None:
    """
    Validate password strength.
    Rules:
    - At least one number
    """
    if not re.search(r"\d", password):
        return "Passordet må inneholde minst ett tall"
    return None


def validate_email(email: str) -> str | None:
    """
    Validate email format.

    Returns:
        str: Error message if invalid, None if valid.
    """
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    if not re.match(pattern, email):
        return "Ugyldig e-postadresse"
    return None


router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request/Response models ───────────────────────────────
class RegisterRequest(BaseModel):
    """
    Request model for user registration.

    Attributes:
        name (str): Display name of the user.
        email (str): Email address used for login.
        password (str): Plain text password (will be hashed).
    """
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """
    Request model for user login.

    Attributes:
        email (str): Registered email address.
        password (str): Plain text password.
    """
    email: str
    password: str


class TokenResponse(BaseModel):
    """
    Response model returned after successful login or registration.

    Attributes:
        access_token (str): JWT token to use in Authorization header.
        user_name (str): Display name of the logged in user.
    """
    access_token: str
    user_name: str


# ── Endpoints ─────────────────────────────────────────────
@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Validates email format and password strength before creating the user.
    Checks if email is already registered.
    Hashes the password before storing.

    Args:
        req (RegisterRequest): Contains name, email and password.
        db (Session): Database session.

    Returns:
        TokenResponse: JWT token and user name on success.

    Raises:
        HTTPException 400: If validation fails or email already exists.
    """
    # Validate email format
    email_error = validate_email(req.email)
    if email_error:
        raise HTTPException(status_code=400, detail=email_error)

    # Validate password strength
    password_error = validate_password(req.password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    # Check if email already exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-postadressen er allerede registrert")

    user = User(
        name=req.name,
        email=req.email,
        hashed_password=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return TokenResponse(access_token=token, user_name=user.name)


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Log in with email and password.

    Verifies the password against the stored hash.
    Returns a JWT token on success.

    Args:
        req (LoginRequest): Contains email and password.
        db (Session): Database session.

    Returns:
        TokenResponse: JWT token and user name on success.

    Raises:
        HTTPException 401: If email or password is incorrect.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ugyldig e-post eller passord")

    token = create_token(user.id)
    return TokenResponse(access_token=token, user_name=user.name)


@router.get("/me")
def me(db: Session = Depends(get_db)):
    """Placeholder endpoint — will be protected in a future step."""
    return {"message": "this endpoint will be protected in next step"}