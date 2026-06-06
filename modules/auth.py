"""
AARKAAI Backend – Authentication Module

Standalone JWT-based Authentication system for user login, registration, and API security.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_session, UserAccount, SessionLocal

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for extracting the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token containing the user's ID."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> UserAccount:
    """
    FastAPI Dependency to ensure a valid JWT token is present and the user exists.
    Extracts the user_id from the token payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    return user


# ─── Register / Login helpers ─────────────────────────────────────────────────


def register_user(email: str, password: str, name: Optional[str] = None) -> dict:
    """
    Create a new user. Raises ValueError on duplicate email or weak password.
    Returns the JWT auth payload dict.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 6 characters")

    session = SessionLocal()
    try:
        existing = session.query(UserAccount).filter(
            UserAccount.email == email.lower().strip()
        ).first()
        if existing:
            raise ValueError("An account with this email already exists")

        user_id = str(uuid.uuid4())
        user = UserAccount(
            id=user_id,
            email=email.lower().strip(),
            password_hash=get_password_hash(password),
            name=name or None,
        )
        session.add(user)
        session.commit()

        token = create_access_token({"sub": user_id, "email": user.email})
        logger.info("Registered new user: %s (%s)", user.email, user_id)
        return {"access_token": token, "token_type": "bearer", "user_id": user_id, "name": name}
    except ValueError:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logger.error("register_user failed: %s", exc)
        raise
    finally:
        session.close()


def login_user(email: str, password: str) -> dict:
    """
    Verify credentials and return a new JWT. Raises ValueError on bad credentials.
    """
    session = SessionLocal()
    try:
        user = session.query(UserAccount).filter(
            UserAccount.email == email.lower().strip()
        ).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is disabled")

        token = create_access_token({"sub": user.id, "email": user.email})
        logger.info("User logged in: %s", user.email)
        return {"access_token": token, "token_type": "bearer", "user_id": user.id, "name": user.name}
    except ValueError:
        raise
    except Exception as exc:
        logger.error("login_user failed: %s", exc)
        raise
    finally:
        session.close()
