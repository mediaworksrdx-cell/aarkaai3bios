"""
Integration tests for the AARKAAI REST API.
Requires the full app with mocked pipeline and in-memory DB.
Mark: @pytest.mark.integration
"""
import pytest
from unittest.mock import patch, MagicMock


pytestmark = pytest.mark.integration


# ─── /health ─────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200

    def test_response_schema(self, test_client):
        data = test_client.get("/health").json()
        assert "status" in data
        assert "version" in data
        assert "modules" in data

    def test_version_is_not_2xx(self, test_client):
        """Ensures the version string drift fix is working."""
        data = test_client.get("/health").json()
        assert data["version"] != "2.0.0"

    def test_version_is_3xx(self, test_client):
        data = test_client.get("/health").json()
        assert data["version"].startswith("3.")


# ─── / (root) ────────────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_returns_200(self, test_client):
        resp = test_client.get("/")
        assert resp.status_code == 200

    def test_version_not_2xx(self, test_client):
        data = test_client.get("/").json()
        assert data.get("version") != "2.0.0"


# ─── /auth/register ──────────────────────────────────────────────────────────

class TestAuthRegister:
    def test_missing_fields_returns_422(self, test_client):
        resp = test_client.post("/auth/register", json={})
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, test_client):
        resp = test_client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "name": "Test User"
        })
        assert resp.status_code == 422

    def test_short_password_returns_422(self, test_client):
        resp = test_client.post("/auth/register", json={
            "email": "user@example.com",
            "password": "123",
            "name": "Test User"
        })
        assert resp.status_code == 422


# ─── /prompt ─────────────────────────────────────────────────────────────────

class TestPromptEndpoint:
    def test_unauthenticated_guest_allowed(self, test_client, mock_pipeline):
        """Guest (visitor) access is allowed on /prompt."""
        resp = test_client.post("/prompt", json={"query": "hello"})
        # Should succeed or return auth error — NOT 422 or 500
        assert resp.status_code not in (422, 500)

    def test_missing_query_returns_422(self, test_client):
        resp = test_client.post("/prompt", json={})
        assert resp.status_code == 422

    def test_empty_query_returns_422(self, test_client):
        resp = test_client.post("/prompt", json={"query": ""})
        assert resp.status_code == 422
