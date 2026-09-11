from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import User

settings = get_settings()
password_hasher = PasswordHasher()
ALLOWED_ROLES = {"CITIZEN", "OFFICER", "ADMIN"}


class AuthenticationError(ValueError):
    pass


class EmailAlreadyRegistered(ValueError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(db: Session, name: str, email: str, password: str, role: str = "CITIZEN") -> User:
    normalized = normalize_email(email)
    normalized_role = role.strip().upper()
    if normalized_role not in ALLOWED_ROLES:
        raise ValueError("Unsupported account role.")

    existing = db.scalar(select(User).where(func.lower(User.email) == normalized))
    if existing:
        raise EmailAlreadyRegistered("An account with this email address already exists.")

    user = User(
        name=name.strip(),
        email=normalized,
        password_hash=password_hasher.hash(password),
        role=normalized_role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegistered("An account with this email address already exists.") from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    normalized = normalize_email(email)
    user = db.scalar(select(User).where(func.lower(User.email) == normalized))
    if not user:
        raise AuthenticationError("Invalid email or password.")
    try:
        password_hasher.verify(user.password_hash, password)
    except VerifyMismatchError as exc:
        raise AuthenticationError("Invalid email or password.") from exc
    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = password_hasher.hash(password)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


def create_session_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_exp_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_session_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Session is invalid or expired.") from exc
