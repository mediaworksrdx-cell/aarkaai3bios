"""
AARKAAI Backend - Code Mode & Approval Router
"""
from __future__ import annotations

import logging
import pydantic
from fastapi import APIRouter, Depends, HTTPException

import modules.auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/codemode", tags=["codemode"])


class ApprovalActionRequest(pydantic.BaseModel):
    approval_id: str
    decision: str  # "APPROVED" | "REJECTED"
    selected_master_strategy: str | None = None


@router.post("/approve")
async def codemode_approve(
    req: ApprovalActionRequest,
    current_user=Depends(modules.auth.get_current_user)
):
    """
    Resolves an in-flight tool approval gate (Approve or Reject).
    Atomic Compare-And-Swap resolution across multi-worker deployments.
    """
    from modules.approval_store import get_approval_store
    store = get_approval_store()
    user_id = getattr(current_user, "id", "default") if current_user else "default"
    clean_decision = req.decision.upper()
    if clean_decision in ("APPROVE", "APPROVED"):
        normalized = "APPROVED"
    elif clean_decision in ("DENY", "DENIED", "REJECT", "REJECTED"):
        normalized = "REJECTED"
    else:
        normalized = req.decision
    resp = store.resolve_request(req.approval_id, user_id=user_id, decision=normalized)
    if resp.status == "unauthorized":
        raise HTTPException(status_code=403, detail=resp.message)
    if resp.status == "invalid":
        raise HTTPException(status_code=400, detail=resp.message)
    return {
        "approval_id": resp.approval_id,
        "status": resp.status,
        "message": resp.message,
        "action_hash": resp.action_hash
    }
