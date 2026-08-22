"""
AARKAAI Backend – Health & Monitoring Routes
"""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])

# Module initialization tracking (populated by main.py startup)
_module_status: dict[str, bool] = {}
_start_time: float = time.time()


def set_module_status(statuses: dict[str, bool]):
    """Called from main.py startup to register component health."""
    global _module_status
    _module_status = statuses


@router.get("/health")
async def health_check():
    """Basic health check with component status."""
    uptime = round(time.time() - _start_time, 1)
    all_ok = all(_module_status.values()) if _module_status else True
    return {
        "status": "ok" if all_ok else "degraded",
        "uptime_seconds": uptime,
        "components": _module_status,
    }


@router.get("/health/live")
async def liveness():
    """Kubernetes-style liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    """Kubernetes-style readiness probe — checks all dependencies."""
    checks = {}
    
    # Check database
    try:
        from database import SessionLocal
        session = SessionLocal()
        session.execute("SELECT 1" if hasattr(session, 'execute') else None)
        session.close()
        checks["database"] = True
    except Exception:
        checks["database"] = False
    
    # Check MongoDB
    try:
        import config
        if config.MONGODB_URI:
            from modules.mongo_client import get_mongo_client
            client = get_mongo_client()
            client.admin.command("ping")
            checks["mongodb"] = True
        else:
            checks["mongodb"] = "not_configured"
    except Exception:
        checks["mongodb"] = False
    
    all_ok = all(v is True or v == "not_configured" for v in checks.values())
    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
    }
