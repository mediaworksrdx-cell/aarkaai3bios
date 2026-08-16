"""
AARKAAI Backend – Authentication Module (Production-Grade)

Dual-token JWT architecture:
  - Short-lived Access Token  (15 min default)
  - Long-lived Refresh Token  (30 days default)

Supports Redis-backed token revocation for secret rotation
and forced logout scenarios.

Password hashing: bcrypt via passlib (with legacy SHA256 fallback).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import os
import uuid

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, API_KEY, API_KEY_HEADER
from database import get_session, UserAccount, SessionLocal

logger = logging.getLogger(__name__)

# ─── Token Expiry Configuration ──────────────────────────────────────────────
# Access token: short-lived (30 min for security)
ACCESS_TOKEN_MINUTES = int(os.getenv("AARKAAI_ACCESS_TOKEN_MINUTES", "30"))
# Refresh token: long-lived (default 30 days)
REFRESH_TOKEN_DAYS = int(os.getenv("AARKAAI_REFRESH_TOKEN_DAYS", "30"))

# Password hashing context (bcrypt, salted)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme (auto_error=False to allow checking X-API-Key fallback)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# ─── Redis Token Revocation Store ────────────────────────────────────────────
_redis_revocation = None
_redis_checked = False


def _get_revocation_store():
    """Lazy-init Redis connection for token blacklisting. Returns None if unavailable."""
    global _redis_revocation, _redis_checked
    if _redis_checked:
        return _redis_revocation
    _redis_checked = True
    try:
        import redis as redis_lib
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _redis_revocation = redis_lib.from_url(redis_url, socket_connect_timeout=1, decode_responses=True)
        _redis_revocation.ping()
        logger.info("Token revocation store: using Redis backend (%s)", redis_url)
    except Exception:
        _redis_revocation = None
        logger.info("Token revocation store: Redis unavailable, revocation disabled")
    return _redis_revocation


def _is_token_revoked(jti: str) -> bool:
    """Check if a token JTI has been revoked."""
    r = _get_revocation_store()
    if r is None:
        return False
    try:
        return r.exists(f"revoked:{jti}") == 1
    except Exception:
        return False


def revoke_token(jti: str, expires_in_seconds: int = 86400 * 31) -> bool:
    """
    Add a token JTI to the revocation blacklist.
    TTL defaults to 31 days (slightly longer than max refresh token lifetime).
    """
    r = _get_revocation_store()
    if r is None:
        logger.warning("Cannot revoke token: Redis unavailable")
        return False
    try:
        r.setex(f"revoked:{jti}", expires_in_seconds, "1")
        return True
    except Exception as exc:
        logger.error("Token revocation failed: %s", exc)
        return False


# ─── Password Hashing ────────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Support legacy SHA256 hashes gracefully while using bcrypt for new/upgraded passwords
    if len(hashed_password) == 64 and not hashed_password.startswith("$"):
        import hashlib
        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == hashed_password
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ─── Token Generation ────────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token with type='access' and unique JTI."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived JWT refresh token with type='refresh' and unique JTI."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_DAYS))
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def refresh_access_token(refresh_token_str: str) -> dict:
    """
    Validate a refresh token, check revocation, and issue a fresh access token.
    Returns {"access_token": ..., "token_type": "bearer"}.
    Raises HTTPException on invalid/expired/revoked tokens.
    """
    try:
        payload = jwt.decode(refresh_token_str, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired. Please login again.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token.")

    jti = payload.get("jti", "")
    if _is_token_revoked(jti):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token claims.")

    new_access = create_access_token(data={"sub": user_id})
    return {"access_token": new_access, "token_type": "bearer"}


# ─── Static System Users ─────────────────────────────────────────────────────

SERVICE_USER = UserAccount(
    id="service_api_user",
    email="service@aarkaai.com",
    name="Service API User",
    role="user",
    is_active=1,
)

GUEST_USER = UserAccount(
    id="guest_visitor",
    email="visitor@aarkaai.com",
    name="Guest Visitor",
    role="user",
    is_active=1,
)


# ─── Authentication Dependencies ─────────────────────────────────────────────


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> UserAccount:
    """
    FastAPI Dependency to ensure authentication via:
    1. X-API-Key header (for service-to-service requests like FinGenIQ)
    2. Bearer JWT Token (for logged-in web/mobile users)
    3. Guest Visitor fallback (for unauthenticated web chat visitors)
    """
    # 1. Check API Key authentication first
    provided_api_key = request.headers.get(API_KEY_HEADER, "")
    if API_KEY and provided_api_key == API_KEY:
        return SERVICE_USER

    # 2. Check JWT Bearer token authentication
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

            # Reject refresh tokens used as access tokens
            token_type = payload.get("type", "access")
            if token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Cannot use a refresh token for API access.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check revocation
            jti = payload.get("jti", "")
            if jti and _is_token_revoked(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id: str = payload.get("sub")
            if user_id:
                import config
                if config.MONGODB_URI:
                    from modules.mongo_repository import UserRepo
                    mongo_user_doc = UserRepo.get_by_id(user_id)
                    if mongo_user_doc and mongo_user_doc.get("is_active"):
                        return UserAccount(
                            id=mongo_user_doc["id"],
                            email=mongo_user_doc["email"],
                            name=mongo_user_doc.get("name", ""),
                            role=mongo_user_doc.get("role", "user"),
                            is_active=mongo_user_doc.get("is_active", 1)
                        )
                user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
                if user and user.is_active:
                    return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except HTTPException:
            raise
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Missing credentials -> 401 Unauthorized
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid Bearer token or API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    provided_api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_session),
) -> UserAccount:
    """
    FastAPI Dependency that resolves the authenticated user if credentials are provided,
    otherwise gracefully falls back to GUEST_USER (for public guest chat/stream endpoints).
    """
    try:
        return await get_current_user(token=token, provided_api_key=provided_api_key, db=db)
    except HTTPException:
        return GUEST_USER


async def require_admin(
    current_user: UserAccount = Depends(get_current_user),
) -> UserAccount:
    """
    FastAPI Dependency that ensures the authenticated user has admin role.
    Use this on admin-only endpoints (knowledge, stats, subscription upgrade, metrics).
    """
    if getattr(current_user, 'role', 'user') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


# ─── Register / Login helpers ─────────────────────────────────────────────────


def register_user(email: str, password: str, name: Optional[str] = None) -> dict:
    """
    Create a new user. Raises ValueError on duplicate email or weak password.
    Returns the dual-token auth payload dict.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

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

        access = create_access_token({"sub": user_id})
        refresh = create_refresh_token({"sub": user_id})
        logger.info("Registered new user: %s (%s)", user.email, user_id)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user_id": user_id,
            "name": name,
        }
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
    Verify credentials and return dual-token payload. Raises ValueError on bad credentials.
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

        access = create_access_token({"sub": user.id})
        refresh = create_refresh_token({"sub": user.id})
        logger.info("User logged in: %s", user.email)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name,
        }
    except ValueError:
        raise
    except Exception as exc:
        logger.error("login_user failed: %s", exc)
        raise
    finally:
        session.close()

