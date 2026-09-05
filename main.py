"""
AARKAAI Backend – FastAPI Application (Production-Ready)

Endpoints:
  POST /prompt          – Main query endpoint (uses pipeline)
  GET  /health          – System health check
  GET  /                – Welcome / info
  POST /admin/knowledge – Add RAG knowledge
  POST /admin/user-memory – Set user memory
  POST /rlhf            – Submit RLHF feedback
  GET  /admin/stats     – Database statistics
  GET  /metrics         – Operational metrics
"""
from __future__ import annotations

import os

# Prevent OpenMP and MKL thread conflicts that cause segmentation faults
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Import llama_cpp first to avoid DLL loading conflicts on Windows when torch/sentence-transformers are imported first
try:
    import llama_cpp
except ImportError:
    pass

import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import fastapi
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import modules.auth
from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALLOWED_ORIGINS,
    BASE_URL,
    ENVIRONMENT,
    HOST,
    IS_PRODUCTION,
    LOG_LEVEL,
    PORT,
    WORKERS,
)
from schemas import (
    AdminKnowledgeRequest,
    AdminUserMemoryRequest,
    GoogleAuthRequest,
    LogoutRequest,
    RLHFRequest,
    RefreshRequest,
    HealthResponse,
    PromptRequest,
    PromptResponse,
    SkillModel,
    StrategyRequest,
    StrategyResponse,
    TestRequestModel,
    TokenResponse,
    UserCreate,
    UserSettingsUpdate,
    UserSettingsResponse,
)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s │ %(name)-28s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aarkaai")

# ─── Operational Metrics ──────────────────────────────────────────────────────
_metrics = {
    "requests_total": 0,
    "requests_failed": 0,
    "total_processing_time": 0.0,
    "startup_time": None,
}

# ─── Module status tracker ────────────────────────────────────────────────────
_module_status: dict[str, str] = {}


def _init_modules() -> None:
    """Initialise all subsystems at startup."""
    global _module_status

    # 1. Database
    try:
        from database import init_db
        init_db()
        _module_status["database"] = "ok"
        logger.info("✓ Database initialised")
    except Exception as exc:
        _module_status["database"] = f"error: {exc}"
        logger.error("✗ Database init failed: %s", exc)

    # 2. Embedding model (shared across modules)
    embed_fn = None
    try:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL_NAME

        _st_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
        embed_fn = lambda text: _st_model.encode(text, normalize_embeddings=True)  # noqa: E731
        _module_status["embeddings"] = "ok"
        logger.info("✓ Embedding model loaded (%s)", EMBEDDING_MODEL_NAME)
    except Exception as exc:
        _module_status["embeddings"] = f"error: {exc}"
        logger.error("✗ Embedding model failed: %s", exc)

    # 3. Semantic Filter
    try:
        from modules import semantic_filter
        semantic_filter.init(embed_fn)
        _module_status["semantic_filter"] = "ok"
        logger.info("✓ Semantic filter ready")
    except Exception as exc:
        _module_status["semantic_filter"] = f"error: {exc}"
        logger.error("✗ Semantic filter init failed: %s", exc)

    # 4. AARKAA-3B Engine
    try:
        from modules import aarkaa_engine
        aarkaa_engine.init()
        status = "ok (live)" if aarkaa_engine.is_available() else "ok (stub)"
        _module_status["aarkaa_engine"] = status
        logger.info("✓ AARKAA-3B engine: %s", status)
    except Exception as exc:
        _module_status["aarkaa_engine"] = f"error: {exc}"
        logger.error("✗ AARKAA-3B init failed: %s", exc)

    # 5. RAG Engine
    try:
        from modules import rag
        reranker_fn = None
        try:
            from sentence_transformers import CrossEncoder
            from config import RERANKER_MODEL_NAME
            
            logger.info("Loading RAG reranker model: %s", RERANKER_MODEL_NAME)
            _reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
            reranker_fn = lambda q, d: float(_reranker_model.predict([(q, d)])[0])
            logger.info("✓ RAG reranker model loaded successfully")
        except Exception as r_exc:
            logger.warning("RAG reranker model load failed (falling back to cosine-only): %s", r_exc)

        rag.init(embed_fn, reranker_fn)
        _module_status["rag"] = "ok"
        logger.info("✓ RAG engine ready (%d entries)", rag.get_entry_count())
    except Exception as exc:
        _module_status["rag"] = f"error: {exc}"
        logger.error("✗ RAG init failed: %s", exc)

    # 5b. Architecture Knowledge Indexing (into RAG)
    try:
        from modules.architecture_knowledge import index_architecture_knowledge
        index_architecture_knowledge(embed_fn)
        logger.info("✓ Architecture knowledge indexed")
    except Exception as exc:
        logger.warning("✗ Architecture knowledge indexing failed: %s", exc)

    # 6. Auto-Learn
    try:
        from modules import auto_learn
        auto_learn.init(embed_fn)
        _module_status["auto_learn"] = "ok"
        logger.info("✓ Auto-learn system ready")
    except Exception as exc:
        _module_status["auto_learn"] = f"error: {exc}"
        logger.error("✗ Auto-learn init failed: %s", exc)

    # 7. Finance (stateless – just verify import)
    try:
        from modules import finance  # noqa: F401
        _module_status["finance"] = "ok"
        logger.info("✓ Finance module available")
    except Exception as exc:
        _module_status["finance"] = f"error: {exc}"
        logger.error("✗ Finance module failed: %s", exc)

    # 8. Web Search (stateless – verify import)
    try:
        from modules import web_search  # noqa: F401
        _module_status["web_search"] = "ok"
        logger.info("✓ Web search module available")
    except Exception as exc:
        _module_status["web_search"] = f"error: {exc}"
        logger.error("✗ Web search module failed: %s", exc)

    # 9. Memory (stateless – verify import)
    try:
        from modules import memory  # noqa: F401
        _module_status["memory"] = "ok"
        logger.info("✓ Memory system available")
    except Exception as exc:
        _module_status["memory"] = f"error: {exc}"
        logger.error("✗ Memory module failed: %s", exc)

    # 10. Subscription (freemium gate)
    try:
        from modules import subscription
        subscription.init()
        _module_status["subscription"] = "ok"
        logger.info("✓ Subscription system ready")
    except Exception as exc:
        _module_status["subscription"] = f"error: {exc}"
        logger.error("✗ Subscription module failed: %s", exc)

    # 11. Create workspace directory for sandboxed tools
    try:
        from config import SAFE_WORK_DIR
        SAFE_WORK_DIR.mkdir(parents=True, exist_ok=True)
        _module_status["workspace"] = "ok"
        logger.info("✓ Workspace directory: %s", SAFE_WORK_DIR)
    except Exception as exc:
        _module_status["workspace"] = f"error: {exc}"
        logger.error("✗ Workspace dir failed: %s", exc)

    # 12. Skill Registry (loads SKILL.md files for the coordinator agent)
    try:
        from modules.tools.skill_tools import init_skill_registry
        import os
        skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
        reg = init_skill_registry(skills_dir)
        skill_count = len(reg.skills)
        _module_status["skills"] = f"ok ({skill_count} skills)"
        logger.info("✓ Skill registry: %d skills loaded", skill_count)
    except Exception as exc:
        _module_status["skills"] = f"error: {exc}"
        logger.error("✗ Skill registry failed: %s", exc)


# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  AARKAAI Backend – Starting up (%s) …", ENVIRONMENT)
    logger.info("=" * 60)

    start = time.perf_counter()
    _init_modules()

    ok_count = sum(1 for v in _module_status.values() if v.startswith("ok"))
    total = len(_module_status)
    startup_secs = round(time.perf_counter() - start, 2)

    _metrics["startup_time"] = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Startup complete: %d/%d modules operational (%.1fs)",
        ok_count, total, startup_secs,
    )

    # Fail fast in production if critical modules are down
    if IS_PRODUCTION:
        critical = ["database", "embeddings", "aarkaa_engine"]
        for mod in critical:
            status = _module_status.get(mod, "missing")
            if not status.startswith("ok"):
                logger.critical(
                    "CRITICAL module '%s' is DOWN (%s) — aborting production startup!",
                    mod, status,
                )
                sys.exit(1)

    logger.info("=" * 60)
    yield

    # Graceful shutdown
    logger.info("AARKAAI Backend – Shutting down")
    try:
        from database import engine
        engine.dispose()
        logger.info("Database connections closed")
    except Exception:
        pass


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AARKAAI",
    description=(
        "AARKAA-3B powered multilingual AI backend with semantic routing, "
        "finance data, RAG knowledge, web search, memory, and auto-learning."
    ),
    version="2.0.0",
    lifespan=lifespan,
    # Disable Swagger UI in production
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
)

# ─── Middleware Stack (order matters: outermost first) ────────────────────────

# 1. Request tracking (outermost — catches everything)
from middleware import RequestTrackingMiddleware
app.add_middleware(RequestTrackingMiddleware)

# 2. Rate limiting
from middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# 3. API key authentication
from middleware import APIKeyMiddleware
app.add_middleware(APIKeyMiddleware)

# 4. Response caching (POST /prompt → Redis, TTL=1h)
from middleware import ResponseCacheMiddleware
app.add_middleware(ResponseCacheMiddleware)

# 5. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Error Handler ────────────────────────────────────────────────────────────


@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error("Unhandled error: %s", exc, exc_info=True)
        _metrics["requests_failed"] += 1
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again or contact support."},
        )


import modules.errors
from fastapi.encoders import jsonable_encoder

@app.exception_handler(fastapi.exceptions.RequestValidationError)
async def validation_exception_handler(request: Request, exc: fastapi.exceptions.RequestValidationError):
    return await modules.errors.validation_exception_handler(request, exc)


# ─── Authentication Endpoints ───────────────────────────────────────────────────

@app.post("/auth/register", response_model=TokenResponse, tags=["auth"])
def register_user(req: UserCreate):
    """Register a new user account. Returns access + refresh tokens."""
    import uuid
    import config
    from modules.auth import get_password_hash, create_access_token, create_refresh_token
    
    if config.MONGODB_URI:
        from modules.mongo_repository import UserRepo
        existing_doc = UserRepo.get_by_email(req.email)
        if existing_doc:
            raise HTTPException(status_code=400, detail="Email already registered")
        user_id = str(uuid.uuid4())
        pwd_hash = get_password_hash(req.password)
        UserRepo.create_user(user_id=user_id, email=req.email, password_hash=pwd_hash, name=req.name)
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user_id,
            "name": req.name,
        }

    from database import SessionLocal, UserAccount
    db = SessionLocal()
    try:
        # Check if email exists
        if db.query(UserAccount).filter(UserAccount.email == req.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
            
        # Create user
        user_id = str(uuid.uuid4())
        new_user = UserAccount(
            id=user_id,
            email=req.email,
            password_hash=get_password_hash(req.password),
            name=req.name
        )
        db.add(new_user)
        db.commit()
        
        # Create dual tokens
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user_id,
            "name": req.name,
        }
    finally:
        db.close()


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_user(req: UserCreate):
    """Login and get access + refresh JWT tokens."""
    import config
    from modules.auth import verify_password, create_access_token, create_refresh_token

    if config.MONGODB_URI:
        from modules.mongo_repository import UserRepo
        user_doc = UserRepo.get_by_email(req.email)
        if not user_doc:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        is_valid, needs_rehash = verify_password(req.password, user_doc.get("password_hash", ""))
        if not is_valid:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        # SEC-H2 FIX: Auto-rehash legacy SHA-256 passwords to bcrypt on successful login
        if needs_rehash:
            from modules.auth import get_password_hash
            UserRepo.update_password_hash(user_doc["id"], get_password_hash(req.password))
        user_id = user_doc["id"]
        name = user_doc.get("name", "")
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user_id,
            "name": name,
        }

    from database import SessionLocal, UserAccount
    db = SessionLocal()
    try:
        user = db.query(UserAccount).filter(UserAccount.email == req.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        is_valid, needs_rehash = verify_password(req.password, user.password_hash)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        # SEC-H2 FIX: Auto-rehash legacy SHA-256 passwords to bcrypt on successful login
        if needs_rehash:
            from modules.auth import get_password_hash
            user.password_hash = get_password_hash(req.password)
            db.commit()
            
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name,
        }
    finally:
        db.close()

@app.post("/auth/visitor-token", response_model=TokenResponse, tags=["auth"])
def issue_visitor_token():
    """Issue a temporary anonymous visitor JWT without requiring credentials.
    This eliminates the need to embed any password in the frontend bundle."""
    import uuid
    import config
    from modules.auth import get_password_hash, create_access_token, verify_password
    import os

    visitor_email = os.getenv("VISITOR_EMAIL", "visitor@aarkaai.com")
    visitor_password = os.getenv("VISITOR_PASSWORD", "")
    if not visitor_password:
        # Generate deterministic dev-only password from SECRET_KEY (never hardcoded)
        import hashlib
        from config import SECRET_KEY
        visitor_password = hashlib.sha256(f"visitor-{SECRET_KEY}".encode()).hexdigest()[:24]

    if config.MONGODB_URI:
        from modules.mongo_repository import UserRepo
        user_doc = UserRepo.get_by_email(visitor_email)
        if user_doc:
            user_id = user_doc["id"]
        else:
            user_id = str(uuid.uuid4())
            pwd_hash = get_password_hash(visitor_password)
            UserRepo.create_user(user_id=user_id, email=visitor_email, password_hash=pwd_hash, name="Web Visitor")
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer", "user_id": user_id, "name": "Web Visitor"}

    from database import SessionLocal, UserAccount
    db = SessionLocal()
    try:
        user = db.query(UserAccount).filter(UserAccount.email == visitor_email).first()
        if not user:
            user_id = str(uuid.uuid4())
            new_user = UserAccount(
                id=user_id,
                email=visitor_email,
                password_hash=get_password_hash(visitor_password),
                name="Web Visitor"
            )
            db.add(new_user)
            db.commit()
        else:
            user_id = user.id
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer", "user_id": user_id, "name": "Web Visitor"}
    finally:
        db.close()

# ─── Token Refresh & Logout ──────────────────────────────────────────────────

@app.post("/auth/refresh", response_model=TokenResponse, tags=["auth"])
def refresh_token_endpoint(req: RefreshRequest):
    """Exchange a valid refresh token for a new short-lived access token."""
    from modules.auth import refresh_access_token
    return refresh_access_token(req.refresh_token)


@app.post("/auth/logout", tags=["auth"])
def logout_endpoint(req: LogoutRequest):
    """Revoke access and/or refresh tokens (adds JTI to Redis blacklist)."""
    import jwt as pyjwt
    from config import SECRET_KEY, JWT_ALGORITHM
    from modules.auth import revoke_token

    revoked = []
    for token_str in [req.access_token, req.refresh_token]:
        if not token_str:
            continue
        try:
            payload = pyjwt.decode(token_str, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            if jti and revoke_token(jti):
                revoked.append(payload.get("type", "unknown"))
        except pyjwt.PyJWTError:
            pass  # Silently skip invalid/expired tokens

    return {"detail": f"Revoked {len(revoked)} token(s)", "revoked_types": revoked}


# ─── GitHub OAuth ────────────────────────────────────────────────────────────

def _get_github_redirect_uri(request: Request) -> str:
    """Construct redirect_uri matching GitHub OAuth App settings."""
    import os
    if os.getenv("GITHUB_REDIRECT_URI"):
        return os.environ["GITHUB_REDIRECT_URI"]

    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    clean_host = forwarded_host.split(":")[0].lower()

    if "synthetixanalytics.com" in clean_host:
        return "https://synthetixanalytics.com/aarkaai/oauthcallback"
    elif clean_host in {"localhost", "127.0.0.1"} or clean_host.startswith("192.168.") or clean_host.startswith("10.") or clean_host.startswith("136.85."):
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        return f"{scheme}://{forwarded_host}/auth/github/callback"
    else:
        return "https://aarka-ai.com/auth/github/callback"


@app.get("/auth/github/login", tags=["auth"])
def github_login(request: Request):
    """Redirect to GitHub OAuth screen with CSRF state parameter."""
    import secrets
    from config import GITHUB_CLIENT_ID, IS_PRODUCTION
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub Client ID is not configured.")
    state = secrets.token_urlsafe(32)
    redirect_uri = _get_github_redirect_uri(request)
    scope = "user:email read:user"
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
    )
    is_https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    response = fastapi.responses.RedirectResponse(url=github_auth_url)
    response.set_cookie(
        key="oauth_state", value=state, max_age=600, httponly=True,
        samesite="lax", secure=(IS_PRODUCTION and is_https), path="/"
    )
    return response


@app.get("/auth/github/callback", tags=["auth"])
async def github_callback(code: str, state: str, request: Request):
    """Exchange code for GitHub profile, validate CSRF state, register or sign in user."""
    import httpx
    import uuid
    from config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, OAUTH_REDIRECT_BASE_URL
    from database import SessionLocal, UserAccount
    from modules.auth import create_access_token

    # Validate CSRF state
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=403, detail="OAuth state mismatch — possible CSRF attack.")
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth credentials not configured.")

    redirect_uri = _get_github_redirect_uri(request)

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            error_desc = token_data.get("error_description", "Failed to retrieve GitHub access token.")
            raise HTTPException(status_code=400, detail=error_desc)

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_profile = user_resp.json()
        github_id = user_profile.get("id")
        name = user_profile.get("name") or user_profile.get("login") or "GitHub User"
        email = user_profile.get("email")

        # If primary email is private in GitHub profile, fetch user emails list
        if not email:
            try:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if emails_resp.status_code == 200:
                    emails_data = emails_resp.json()
                    primary_email = next((e["email"] for e in emails_data if e.get("primary")), None)
                    email = primary_email or (emails_data[0]["email"] if emails_data else None)
            except Exception as exc:
                logger.warning("Could not fetch private GitHub emails: %s", exc)

        if not email:
            email = f"{user_profile.get('login', github_id)}@github.com"

        import config
        if config.MONGODB_URI:
            from modules.mongo_repository import UserRepo
            mongo_user = UserRepo.get_by_email(email)
            if not mongo_user:
                user_id = str(uuid.uuid4())
                UserRepo.create_user(user_id=user_id, email=email, password_hash="GITHUB_OAUTH_USER", name=name)
            else:
                user_id = mongo_user["id"]

            jwt_token = create_access_token(data={"sub": user_id})
            cookie_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60

            # SEC-C3 FIX: Do NOT pass JWT token, email, or name in URL query parameters.
            # Tokens in URLs leak via browser history, Referer headers, server logs, and CDN logs.
            # The token is delivered exclusively via HTTP-only secure cookie below.
            from urllib.parse import quote
            safe_name = quote(name, safe="")
            host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "aarka-ai.com"
            scheme = request.headers.get("x-forwarded-proto", "https")
            if "aarka-ai.com" in host:
                target_url = f"{scheme}://{host}/?auth=success&name={safe_name}"
            elif "synthetixanalytics.com" in host:
                target_url = f"{scheme}://{host}/aarkaai?auth=success&name={safe_name}"
            else:
                target_url = f"{OAUTH_REDIRECT_BASE_URL}/?auth=success&name={safe_name}"

            user_agent = request.headers.get("user-agent", "").lower()
            if "android" in user_agent or "okhttp" in user_agent or "mobile" in user_agent:
                # Mobile deep link: token still in URL for app scheme (not exposed to web)
                response = fastapi.responses.RedirectResponse(
                    url=f"aarkaai://auth-callback?auth=success&user_id={user_id}&name={safe_name}&token={jwt_token}"
                )
            else:
                response = fastapi.responses.RedirectResponse(
                    url=target_url
                )
            response.set_cookie(
                key="aarkaai_token", value=jwt_token,
                max_age=cookie_max_age, httponly=True,
                secure=True, samesite="lax", path="/",
            )
            return response

        db = SessionLocal()
        try:
            user = db.query(UserAccount).filter(UserAccount.email == email).first()
            if not user:
                user_id = str(uuid.uuid4())
                user = UserAccount(
                    id=user_id,
                    email=email,
                    password_hash="GITHUB_OAUTH_USER",
                    name=name
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                user_id = user.id

            jwt_token = create_access_token(data={"sub": user_id})
            cookie_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60

            # SEC-C3 FIX: Do NOT pass JWT token, email, or name in URL query parameters.
            from urllib.parse import quote
            safe_name = quote(name, safe="")
            host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "aarka-ai.com"
            scheme = request.headers.get("x-forwarded-proto", "https")
            if "aarka-ai.com" in host:
                target_url = f"{scheme}://{host}/?auth=success&name={safe_name}"
            elif "synthetixanalytics.com" in host:
                target_url = f"{scheme}://{host}/aarkaai?auth=success&name={safe_name}"
            else:
                target_url = f"{OAUTH_REDIRECT_BASE_URL}/?auth=success&name={safe_name}"

            user_agent = request.headers.get("user-agent", "").lower()
            if "android" in user_agent or "okhttp" in user_agent or "mobile" in user_agent:
                # Mobile deep link: token still in URL for app scheme (not exposed to web)
                response = fastapi.responses.RedirectResponse(
                    url=f"aarkaai://auth-callback?auth=success&user_id={user_id}&name={safe_name}&token={jwt_token}"
                )
            else:
                response = fastapi.responses.RedirectResponse(
                    url=target_url
                )
            response.set_cookie(
                key="aarkaai_token", value=jwt_token,
                max_age=cookie_max_age, httponly=True,
                secure=True, samesite="lax", path="/",
            )
            return response
        finally:
            db.close()


# ─── Google OAuth ────────────────────────────────────────────────────────────

def _get_google_redirect_uri(request: Request) -> str:
    """Construct redirect_uri matching Google Cloud Console authorized URIs."""
    import os
    if os.getenv("GOOGLE_REDIRECT_URI"):
        return os.environ["GOOGLE_REDIRECT_URI"]

    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    clean_host = forwarded_host.split(":")[0].lower()

    if "synthetixanalytics.com" in clean_host:
        return "https://synthetixanalytics.com/aarkaai/oauthcallback"
    elif clean_host in {"localhost", "127.0.0.1"} or clean_host.startswith("192.168.") or clean_host.startswith("10.") or clean_host.startswith("136.85."):
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        return f"{scheme}://{forwarded_host}/auth/google/callback"
    else:
        return "https://aarka-ai.com/auth/google/callback"


@app.get("/auth/google/login", tags=["auth"])
def google_login(request: Request):
    """Redirect to Google OAuth 2.0 consent screen."""
    import secrets
    from config import GOOGLE_CLIENT_ID, IS_PRODUCTION
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID is not configured.")

    state = secrets.token_urlsafe(32)
    redirect_uri = _get_google_redirect_uri(request)
    scope = "openid email profile"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        f"&scope={scope}"
        "&access_type=offline"
        "&prompt=consent"
        f"&state={state}"
    )
    is_https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    response = fastapi.responses.RedirectResponse(url=google_auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=(IS_PRODUCTION and is_https),
        samesite="lax",
        path="/"
    )
    return response





@app.get("/auth/google/callback", tags=["auth"])
@app.get("/aarkaai/oauthcallback", tags=["auth"])
async def google_callback(code: str, state: str, request: Request):
    """Exchange OAuth code for Google user profile with PKCE verification."""
    import httpx
    import uuid
    from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OAUTH_REDIRECT_BASE_URL
    from database import SessionLocal, UserAccount
    from modules.auth import create_access_token

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured.")

    # Validate CSRF state
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=403, detail="OAuth state mismatch — possible CSRF attack.")

    # Retrieve PKCE code_verifier
    code_verifier = request.cookies.get("pkce_verifier", "")

    redirect_uri = _get_google_redirect_uri(request)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Exchange code for access token
        token_payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            token_payload["code_verifier"] = code_verifier

        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        id_token = token_data.get("id_token")

        if not access_token and not id_token:
            error_desc = token_data.get("error_description", "Failed to retrieve Google token.")
            raise HTTPException(status_code=400, detail=error_desc)

        # 2. Get user profile from Google
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        profile = user_info_resp.json()

        email = profile.get("email")
        name = profile.get("name") or profile.get("given_name") or "Google User"

        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Google profile.")

        # 3. Authenticate or create user in DB
        db = SessionLocal()
        try:
            user = db.query(UserAccount).filter(UserAccount.email == email).first()
            if not user:
                user_id = str(uuid.uuid4())
                user = UserAccount(
                    id=user_id,
                    email=email,
                    password_hash="GOOGLE_OAUTH_USER",
                    name=name
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            jwt_token = create_access_token(data={"sub": user.id})
            cookie_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60

            # SEC-C3 FIX: Do NOT pass JWT token, email, or name in URL query parameters.
            from urllib.parse import quote
            safe_name = quote(name, safe="")
            host = request.headers.get("host", "aarka-ai.com")
            scheme = request.headers.get("x-forwarded-proto", "https")
            if "aarka-ai.com" in host:
                target_url = f"{scheme}://{host}/?auth=success&name={safe_name}"
            elif "synthetixanalytics.com" in host:
                target_url = f"{scheme}://{host}/aarkaai?auth=success&name={safe_name}"
            else:
                target_url = f"{OAUTH_REDIRECT_BASE_URL}/?auth=success&name={safe_name}"

            user_agent = request.headers.get("user-agent", "").lower()
            if "android" in user_agent or "okhttp" in user_agent or "mobile" in user_agent:
                # Mobile deep link: token still in URL for app scheme (not exposed to web)
                response = fastapi.responses.RedirectResponse(
                    url=f"aarkaai://auth-callback?auth=success&user_id={user.id}&name={safe_name}&token={jwt_token}"
                )
            else:
                response = fastapi.responses.RedirectResponse(
                    url=target_url
                )
            response.set_cookie(
                key="aarkaai_token", value=jwt_token,
                max_age=cookie_max_age, httponly=True,
                secure=True, samesite="lax", path="/",
            )
            return response
        finally:
            db.close()


@app.post("/auth/google/verify", tags=["auth"])
@app.post("/auth/google", tags=["auth"])
async def google_token_verify(payload: GoogleAuthRequest):
    """Directly verify a Google ID token or Access Token from frontend / mobile SDK."""
    import httpx
    import uuid
    from database import SessionLocal, UserAccount
    from modules.auth import create_access_token

    if not payload.id_token and not payload.access_token:
        raise HTTPException(status_code=400, detail="Either id_token or access_token must be provided.")

    email = None
    name = "Google User"

    async with httpx.AsyncClient(timeout=10.0) as client:
        if payload.id_token:
            token_info_resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token}"
            )
            if token_info_resp.status_code == 200:
                data = token_info_resp.json()
                # SEC: Validate audience claim — token must be issued for THIS app
                from config import GOOGLE_CLIENT_ID
                token_aud = data.get("aud", "")
                if GOOGLE_CLIENT_ID and token_aud != GOOGLE_CLIENT_ID:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid Google token: audience mismatch. Token was not issued for this application.",
                    )
                email = data.get("email")
                name = data.get("name") or data.get("given_name") or name


        if not email and payload.access_token:
            user_info_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {payload.access_token}"}
            )
            if user_info_resp.status_code == 200:
                data = user_info_resp.json()
                email = data.get("email")
                name = data.get("name") or data.get("given_name") or name

    if not email:
        raise HTTPException(status_code=401, detail="Invalid Google token or unable to verify identity.")

    db = SessionLocal()
    try:
        user = db.query(UserAccount).filter(UserAccount.email == email).first()
        if not user:
            user_id = str(uuid.uuid4())
            user = UserAccount(
                id=user_id,
                email=email,
                password_hash="GOOGLE_OAUTH_USER",
                name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = create_access_token(data={"sub": user.id})
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name
        }
    finally:
        db.close()


# ─── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/", tags=["info"])
async def root():
    """Welcome / info endpoint."""
    return {
        "name": "AARKAAI",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "description": "AARKAA-3B powered multilingual AI backend",
        "base_url": BASE_URL,
        "endpoints": {
            "POST /auth/register": f"{BASE_URL}/auth/register",
            "POST /auth/login": f"{BASE_URL}/auth/login",
            "POST /prompt": f"{BASE_URL}/prompt",
            "GET /health": f"{BASE_URL}/health",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["info"])
async def health():
    """System health check – reports module status."""
    all_ok = all(v.startswith("ok") for v in _module_status.values())
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        version="2.0.0",
        modules=_module_status,
    )


@app.get("/download/{filename}", tags=["core"])
def download_file(filename: str):
    """
    Securely download a document generated by the AARKAAI skills system.
    Files are retrieved from the sandboxed SAFE_WORK_DIR.
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    from config import SAFE_WORK_DIR

    # Prevent path traversal attacks
    safe_dir = Path(SAFE_WORK_DIR).resolve()
    # Resolve the absolute path of the requested file
    file_path = (safe_dir / filename).resolve()

    # Verify that the path is strictly within the safe workspace directory
    try:
        file_path.relative_to(safe_dir)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied: requested file is outside the allowed directory."
        )

    # Check if the file exists and is indeed a file
    if not file_path.is_file():
        # Fallback: check for files in the same directory that might match the request
        # (e.g. requested 'chennai_startups.pdf' but actual is 'chennai_tech_startups.pdf')
        try:
            import re
            req_words = [w for w in re.split(r'[^a-zA-Z0-9]', Path(filename).stem.lower()) if len(w) > 2]
            req_suffix = Path(filename).suffix.lower()
            
            best_match = None
            best_score = 0
            
            for child in safe_dir.iterdir():
                if child.is_file() and child.suffix.lower() == req_suffix:
                    child_words = [w for w in re.split(r'[^a-zA-Z0-9]', child.stem.lower()) if len(w) > 2]
                    overlap = set(req_words) & set(child_words)
                    score = len(overlap)
                    if score > best_score:
                        best_score = score
                        best_match = child
                        
            if best_match and best_score >= 1:
                file_path = best_match
                filename = best_match.name
        except Exception:
            pass

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found."
        )

    # Return the file as a response
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@app.post("/upload", tags=["core"])
async def upload_file(
    file: fastapi.UploadFile = fastapi.File(...),
    current_user=fastapi.Depends(modules.auth.get_current_user),
):
    """
    Upload a document/file to AARKAAI's sandboxed SAFE_WORK_DIR (workspace).
    Requires JWT auth. Enforces file size and extension whitelist.
    """
    from pathlib import Path
    from config import SAFE_WORK_DIR, MAX_UPLOAD_SIZE_BYTES, ALLOWED_UPLOAD_EXTENSIONS

    # Sanitize the filename to prevent traversal attacks
    filename = Path(file.filename).name
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Extension whitelist
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}",
        )

    safe_dir = Path(SAFE_WORK_DIR).resolve()
    target_path = safe_dir / filename
    total_bytes = 0

    try:
        with open(target_path, "wb") as buffer:
            while chunk := await file.read(8192):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save file.")

    return {
        "status": "success",
        "filename": filename,
        "size_bytes": total_bytes,
        "path": f"/download/{filename}",
    }


@app.get("/subscription", tags=["premium"])
def get_user_subscription(current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Get the current user's subscription details."""
    from modules.subscription import get_subscription_info
    return get_subscription_info(current_user.id)


@app.post("/subscription/upgrade", tags=["premium"])
def upgrade_user_subscription(current_user=fastapi.Depends(modules.auth.require_admin)):
    """Upgrade a user to premium tier. Requires admin role."""
    from modules.subscription import upgrade_user
    try:
        upgrade_user(current_user.id, months=1)
        return {"status": "success", "message": "User upgraded to premium."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Upgrade failed. Contact support.")



@app.get("/metrics", tags=["info"])
async def metrics(current_user=fastapi.Depends(modules.auth.require_admin)):
    """Operational metrics for monitoring (requires auth)."""
    import threading
    from modules.aarkaa_engine import get_status_metadata
    
    total = _metrics["requests_total"]
    failed = _metrics["requests_failed"]
    avg_time = (
        round(_metrics["total_processing_time"] / total, 3) if total > 0 else 0
    )
    success_ratio = (
        round((total - failed) / total, 4) if total > 0 else 1.0
    )
    
    # Expose detailed engine states dynamically
    try:
        engine_status = get_status_metadata()
    except Exception as exc:
        engine_status = {"error": str(exc)}

    return {
        "requests_total": total,
        "requests_failed": failed,
        "success_ratio": success_ratio,
        "avg_processing_time": avg_time,
        "total_processing_time": round(_metrics["total_processing_time"], 3),
        "startup_time": _metrics["startup_time"],
        "environment": ENVIRONMENT,
        "active_threads": threading.active_count(),
        "engine": engine_status,
        "modules": _module_status,
    }


@app.post("/prompt", response_model=PromptResponse, tags=["core"])
async def prompt(
    req: PromptRequest, 
    request: Request,
    current_user = fastapi.Depends(modules.auth.get_optional_user)
):
    """
    Main query endpoint. Supports optional JWT authentication / guest visitors.

    Runs the full pipeline. The user_id is automatically attached from the token or guest identity.
    Uses asyncio.to_thread so the synchronous pipeline does not block the event loop.
    """
    import asyncio
    from pipeline import process_query

    _metrics["requests_total"] += 1

    # Extract execution mode from headers or JSON body (default is production)
    mode = request.headers.get("x-aarkaai-mode", req.mode or "production").lower()

    try:
        # Run the synchronous pipeline in a thread pool to avoid blocking the event loop
        result = await asyncio.to_thread(
            process_query,
            query=req.query,
            user_id=current_user.id,
            session_id=req.session_id,
            mode=mode,
        )
        _metrics["total_processing_time"] += result.processing_time
        return result
    except Exception as exc:
        _metrics["requests_failed"] += 1
        logger.error("Pipeline error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Processing failed. Please try again or contact support.",
        )



@app.post("/prompt/stream", tags=["core"])
async def prompt_stream(
    req: PromptRequest, 
    request: Request,
    current_user = fastapi.Depends(modules.auth.get_optional_user)
):
    """
    Streaming query endpoint. Returns Server-Sent Events (SSE).
    """
    from pipeline import stream_query
    import json

    # Extract execution mode from headers or JSON body (default is production)
    mode = request.headers.get("x-aarkaai-mode", req.mode or "production").lower()

    async def event_generator():
        try:
            async for chunk in stream_query(query=req.query, user_id=current_user.id, session_id=req.session_id, mode=mode, model_override=req.model_override):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            logger.error("Streaming error: %s", exc, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Inference service encountered a temporary error. Please retry.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/strategy", response_model=StrategyResponse, tags=["premium"])
def get_strategy(
    req: StrategyRequest,
    current_user = fastapi.Depends(modules.auth.get_current_user),
):
    """
    Technical analysis + options strategy endpoint.

    Requires JWT Bearer token. Subject to freemium daily limits.
    Returns full technical indicators, consensus signal, and an
    actionable options strategy with defined risk-to-reward ratio.
    """
    import time as _time
    from modules import technical, options_strategy, subscription

    start = _time.perf_counter()

    # 1. Check subscription access
    access = subscription.check_access(current_user.id, feature="strategy")
    if not access["allowed"]:
        return StrategyResponse(
            symbol=req.symbol,
            signal="LOCKED",
            subscription=access,
            processing_time=round(_time.perf_counter() - start, 3),
        )

    # 2. Compute technical indicators
    indicators = technical.compute_indicators(req.symbol, period=req.period)
    if indicators is None:
        raise HTTPException(
            status_code=422,
            detail=f"Could not fetch sufficient historical data for {req.symbol}. "
                   f"Verify the ticker symbol is correct.",
        )

    # 3. Generate signal
    signal = technical.get_signal(indicators)
    tech_summary = technical.format_technical_summary(req.symbol, indicators, signal)

    # 4. Generate strategy
    strategy = options_strategy.generate_strategy(
        symbol=req.symbol,
        indicators=indicators,
        signal=signal,
        risk_reward=req.risk_reward,
    )
    strat_summary = options_strategy.format_strategy_output(strategy) if strategy else ""

    # 5. Record usage
    subscription.record_premium_usage(current_user.id)

    elapsed = round(_time.perf_counter() - start, 3)
    return StrategyResponse(
        symbol=req.symbol,
        signal=signal,
        indicators=indicators,
        strategy=strategy or {},
        technical_summary=tech_summary,
        strategy_summary=strat_summary,
        subscription=access,
        processing_time=elapsed,
    )


@app.post("/admin/knowledge", tags=["admin"])
def admin_add_knowledge(
    req: AdminKnowledgeRequest,
    current_user=fastapi.Depends(modules.auth.require_admin),
):
    """Add a new entry to the RAG knowledge base. Requires JWT auth."""
    from modules import rag
    try:
        rag.store_knowledge(topic=req.title, content=req.content, source=req.source)
        return {"status": "success", "message": "Knowledge added"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/admin/user-memory", tags=["admin"])
def admin_set_user_memory(
    req: AdminUserMemoryRequest,
    current_user=fastapi.Depends(modules.auth.require_admin),
):
    """Set a memory or system prompt for a user. Requires JWT auth."""
    from modules import memory
    try:
        # We store this as a system category memory. The session_id maps to the concept of prompt injecting context
        memory.update_user_memory(
            user_id=req.user_id,
            key=req.session_id,
            value=req.prompt,
            category="system",
        )
        return {"status": "success", "message": "User memory updated"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/rlhf", tags=["core"])
def submit_rlhf_feedback(
    req: RLHFRequest,
    current_user=fastapi.Depends(modules.auth.get_current_user),
):
    """Submit RLHF feedback. Requires JWT auth. user_id is derived from token, not body."""
    from modules import memory
    from database import SessionLocal, ConversationHistory

    db_conv_id = None
    if req.conversation_id is not None:
        try:
            db_conv_id = int(req.conversation_id)
        except ValueError:
            session = SessionLocal()
            try:
                latest_conv = (
                    session.query(ConversationHistory)
                    .filter(ConversationHistory.session_id == req.conversation_id)
                    .order_by(ConversationHistory.timestamp.desc())
                    .first()
                )
                if latest_conv:
                    db_conv_id = latest_conv.id
            except Exception as e:
                logger.error("Failed to lookup conversation by session_id: %s", e)
            finally:
                session.close()

    try:
        # Always use the token's user_id — never trust the body's user_id
        memory.store_rlhf_feedback(
            user_id=current_user.id,
            rating=req.rating,
            conversation_id=db_conv_id,
            correction=req.correction,
        )
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as exc:
        logger.error("RLHF error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/skills", tags=["skills"])
def api_list_skills(current_user=fastapi.Depends(modules.auth.get_current_user)):
    """List all available skills (names and descriptions)."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    return registry.list_skills()

@app.post("/skills", tags=["skills"])
def api_create_skill(req: SkillModel, current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Create a new custom skill."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    user_id = str(current_user.id)
    result = registry.create_skill(req.name, req.content, user_id=user_id)
    if result.startswith("Error"):
        raise HTTPException(status_code=400, detail=result)
    return {"status": "success", "message": result}

@app.get("/skills/{name}", tags=["skills"])
def api_get_skill(name: str, current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Fetch the full content of a skill."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    content = registry.get_skill(name)
    if content.startswith("Error"):
        raise HTTPException(status_code=404, detail=content)
    return {"name": name, "content": content}

@app.put("/skills/{name}", tags=["skills"])
def api_update_skill(name: str, req: SkillModel, current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Update an existing custom skill."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    user_id = str(current_user.id)
    result = registry.update_skill(name, req.content, user_id=user_id)
    if result.startswith("Error"):
        raise HTTPException(status_code=400, detail=result)
    return {"status": "success", "message": result}


@app.post("/skills/{name}/test", tags=["skills"])
def api_test_skill(name: str, req: TestRequestModel, current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Run a test prompt using a specific skill."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    
    skill_content = registry.get_skill(name)
    if skill_content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=skill_content)
    
    from modules.coordinator import stream_task
    import json
    
    context = f"You are testing the custom user skill '{name}'. Below are the guidelines/code templates from the skill:\n\n{skill_content}"
    
    async def event_generator():
        try:
            # stream_task yields status/final data chunks
            for event_type, data in stream_task(req.prompt, context=context):
                yield f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"
        except Exception as exc:
            logger.error("Skill test execution error: %s", exc, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.delete("/skills/{name}", tags=["skills"])
def api_delete_skill(name: str, current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Delete a custom skill."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    user_id = str(current_user.id)
    result = registry.delete_skill(name, user_id=user_id)
    if result.startswith("Error"):
        raise HTTPException(status_code=400, detail=result)
    return {"status": "success", "message": result}


@app.get("/skills/{name}/versions", tags=["skills"])
def api_skill_versions(name: str, current_user=fastapi.Depends(modules.auth.get_current_user)):
    """List version history for a custom skill."""
    from modules.tools.skill_tools import get_registry
    registry = get_registry()
    if not registry:
        raise HTTPException(status_code=500, detail="Skill registry not initialized.")
    user_id = str(current_user.id)
    versions = registry.get_skill_versions(name, user_id=user_id)
    return {"name": name, "versions": versions}


# ─── User Settings ───────────────────────────────────────────────────────────


@app.get("/settings", response_model=UserSettingsResponse, tags=["settings"])
def api_get_settings(current_user=fastapi.Depends(modules.auth.get_current_user)):
    """Retrieve the current user's settings (model, style, theme, language, etc.)."""
    from modules.user_settings import get_user_settings
    return get_user_settings(str(current_user.id))


@app.put("/settings", response_model=UserSettingsResponse, tags=["settings"])
def api_update_settings(
    req: UserSettingsUpdate,
    current_user=fastapi.Depends(modules.auth.get_current_user),
):
    """Update the current user's settings. Only provided fields are changed."""
    from modules.user_settings import update_user_settings

    # Build kwargs from only the fields that were explicitly provided
    updates = req.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No settings provided to update.")

    try:
        return update_user_settings(str(current_user.id), **updates)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/admin/stats", tags=["admin"])
def admin_get_stats(current_user=fastapi.Depends(modules.auth.require_admin)):
    """Get basic database stats. Requires JWT auth."""
    from database import (
        SessionLocal,
        ConversationHistory,
        UserMemory,
        KnowledgeEntry,
        PersonalChat,
        UserKnowledgeProfile,
        RLHFFeedback,
    )
    session = SessionLocal()
    try:
        chat_count = session.query(ConversationHistory).count()
        personal_chat_count = session.query(PersonalChat).count()
        memory_count = session.query(UserMemory).count()
        knowledge_count = session.query(KnowledgeEntry).count()
        profile_count = session.query(UserKnowledgeProfile).count()
        rlhf_count = session.query(RLHFFeedback).count()
        return {
            "conversations": chat_count,
            "personal_chats": personal_chat_count,
            "memories": memory_count,
            "knowledge_entries": knowledge_count,
            "profiles": profile_count,
            "rlhf_feedback": rlhf_count,
        }
    finally:
        session.close()


# ─── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        reload=not IS_PRODUCTION,
        log_level=LOG_LEVEL.lower(),
        access_log=IS_PRODUCTION,
    )
