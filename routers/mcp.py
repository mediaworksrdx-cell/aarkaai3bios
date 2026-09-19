"""
AARKAAI Backend - Model Context Protocol (MCP) Router
"""
from __future__ import annotations

import logging
import pydantic
from fastapi import APIRouter, Depends, HTTPException

import modules.auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp", tags=["mcp"])


class McpToggleRequest(pydantic.BaseModel):
    server_id: str
    enabled: bool


@router.get("/servers")
async def get_mcp_servers(
    current_user=Depends(modules.auth.get_optional_user)
):
    """Returns active MCP server registry, connection statuses, and tool permissions."""
    if current_user is None:
        return {"servers": []}
    from modules.mcp_client import get_mcp_client
    client = get_mcp_client()
    return {"servers": client.get_server_manifests()}


@router.post("/toggle")
async def toggle_mcp_server(
    req: McpToggleRequest,
    current_user=Depends(modules.auth.get_current_user)
):
    """Dynamically enables or disables an MCP server with RBAC and active execution locks."""
    from modules.mcp_client import get_mcp_client
    client = get_mcp_client()
    success, msg = client.toggle_server(req.server_id, req.enabled)
    if not success:
        if "active execution" in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return {"success": success, "message": msg, "server_id": req.server_id, "enabled": req.enabled}
