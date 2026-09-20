"""
Unit tests for FastAPI endpoints:
- POST /codemode/approve
- GET /mcp/servers
- POST /mcp/toggle
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import UserAccount
from modules.auth import get_current_user
from modules.approval_store import get_approval_store


@pytest.fixture
def client():
    fake_user = UserAccount(id="test-user-id", email="test@aarkaai.com", name="Test User", role="user", is_active=1)
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_mcp_servers_endpoint(client):
    res = client.get("/mcp/servers")
    assert res.status_code == 200
    data = res.json()
    assert "servers" in data
    assert isinstance(data["servers"], list)


def test_mcp_toggle_endpoint(client):
    # Toggle nonexistent server
    res = client.post("/mcp/toggle", json={"server_id": "nonexistent_srv", "enabled": True})
    assert res.status_code == 400
    assert "not found" in res.json()["detail"].lower()


def test_codemode_approve_endpoint(client):
    store = get_approval_store()
    rec = store.create_request(
        user_id="default",
        session_id="s1",
        tool_name="BashTool",
        args={"cmd": "git status"},
        risk_level="MEDIUM",
        human_summary="Run git status"
    )

    # Approve
    res = client.post("/codemode/approve", json={"approval_id": rec.approval_id, "decision": "APPROVED"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["approval_id"] == rec.approval_id

    # Second approval attempt on already approved request should return 400 invalid
    res2 = client.post("/codemode/approve", json={"approval_id": rec.approval_id, "decision": "APPROVED"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "approved"
    assert "already in state" in res2.json()["message"].lower()


def test_codemode_approve_invalid_id(client):
    res = client.post("/codemode/approve", json={"approval_id": "appr_invalid12345", "decision": "APPROVED"})
    assert res.status_code == 400
    assert "not found" in res.json()["detail"].lower()
