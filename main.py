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

import logging
import os
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
    RLHFRequest,
    HealthResponse,
    PromptRequest,
    PromptResponse,
    TokenResponse,
    UserCreate,
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

        _st_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
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
        rag.init(embed_fn)
        _module_status["rag"] = "ok"
        logger.info("✓ RAG engine ready (%d entries)", rag.get_entry_count())
    except Exception as exc:
        _module_status["rag"] = f"error: {exc}"
        logger.error("✗ RAG init failed: %s", exc)

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

    # 10. Create workspace directory for sandboxed tools
    try:
        from config import SAFE_WORK_DIR
        SAFE_WORK_DIR.mkdir(parents=True, exist_ok=True)
        _module_status["workspace"] = "ok"
        logger.info("✓ Workspace directory: %s", SAFE_WORK_DIR)
    except Exception as exc:
        _module_status["workspace"] = f"error: {exc}"
        logger.error("✗ Workspace dir failed: %s", exc)


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

# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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
            content={"detail": f"Internal server error: {type(exc).__name__}"},
        )


# ─── Authentication Endpoints ───────────────────────────────────────────────────

@app.post("/auth/register", response_model=TokenResponse, tags=["auth"])
def register_user(req: UserCreate):
    """Register a new user account."""
    import uuid
    from database import SessionLocal, UserAccount
    from modules.auth import get_password_hash, create_access_token
    
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
        
        # Create token
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer", "user_id": user_id, "name": req.name}
    finally:
        db.close()


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_user(req: UserCreate):
    """Login and get a JWT token. Accepts JSON body with email + password."""
    from database import SessionLocal, UserAccount
    from modules.auth import verify_password, create_access_token
    
    db = SessionLocal()
    try:
        user = db.query(UserAccount).filter(UserAccount.email == req.email).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
            
        access_token = create_access_token(data={"sub": user.id})
        return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "name": user.name}
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


@app.get("/metrics", tags=["info"])
async def metrics():
    """Operational metrics for monitoring."""
    total = _metrics["requests_total"]
    avg_time = (
        round(_metrics["total_processing_time"] / total, 3) if total > 0 else 0
    )
    return {
        "requests_total": total,
        "requests_failed": _metrics["requests_failed"],
        "avg_processing_time": avg_time,
        "startup_time": _metrics["startup_time"],
        "environment": ENVIRONMENT,
        "modules": _module_status,
    }


@app.post("/prompt", response_model=PromptResponse, tags=["core"])
def prompt(
    req: PromptRequest, 
    current_user = fastapi.Depends(modules.auth.get_current_user)
):
    """
    Main query endpoint. Requires JWT Bearer token in the header.

    Runs the full pipeline. The user_id is automatically attached from the token.
    """
    from pipeline import process_query

    _metrics["requests_total"] += 1

    try:
        # Pass the verified user_id from the token, not the JSON body
        result = process_query(query=req.query, user_id=current_user.id)
        _metrics["total_processing_time"] += result.processing_time
        return result
    except Exception as exc:
        _metrics["requests_failed"] += 1
        logger.error("Pipeline error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {type(exc).__name__}: {str(exc)}",
        )


@app.post("/prompt/stream", tags=["core"])
async def prompt_stream(
    req: PromptRequest, 
    current_user = fastapi.Depends(modules.auth.get_current_user)
):
    """
    Streaming query endpoint. Returns Server-Sent Events (SSE).
    """
    from pipeline import stream_query
    import json

    async def event_generator():
        try:
            async for chunk in stream_query(query=req.query, user_id=current_user.id):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            logger.error("Streaming error: %s", exc, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/admin/knowledge", tags=["admin"])
def admin_add_knowledge(req: AdminKnowledgeRequest):
    """Add a new entry to the RAG knowledge base."""
    from modules import rag
    try:
        rag.store_knowledge(topic=req.title, content=req.content, source=req.source)
        return {"status": "success", "message": "Knowledge added"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/admin/user-memory", tags=["admin"])
def admin_set_user_memory(req: AdminUserMemoryRequest):
    """Set a memory or system prompt for a user."""
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
def submit_rlhf_feedback(req: RLHFRequest):
    """Submit RLHF feedback and optionally auto-learn from correction."""
    from modules import memory
    try:
        memory.store_rlhf_feedback(
            user_id=req.user_id,
            rating=req.rating,
            conversation_id=req.conversation_id,
            correction=req.correction,
        )
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as exc:
        logger.error("RLHF error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/admin/stats", tags=["admin"])
def admin_get_stats():
    """Get basic database stats."""
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
