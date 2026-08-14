"""
AARKAAI – Test script for OAuth endpoints (GitHub & Google)
Updated: Validates CSRF state, PKCE code_challenge, and env-only credentials.
"""
import sys
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

class TestOAuthEndpoints(unittest.TestCase):

    @patch("config.GITHUB_CLIENT_ID", "test_github_client_id")
    def test_github_login_redirect(self):
        response = client.get("/auth/github/login", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        location = response.headers.get("location", "")
        self.assertIn("github.com/login/oauth/authorize", location)
        self.assertIn("client_id=test_github_client_id", location)
        print("  PASS: /auth/github/login redirects to GitHub correctly")

    @patch("config.GITHUB_CLIENT_ID", "test_github_client_id")
    def test_github_login_sets_state_cookie(self):
        """Verify CSRF state parameter is set in cookie and URL."""
        response = client.get("/auth/github/login", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        location = response.headers.get("location", "")
        self.assertIn("state=", location)
        # Check oauth_state cookie is set
        cookies = response.cookies
        self.assertIn("oauth_state", dict(cookies))
        print("  PASS: /auth/github/login sets CSRF state cookie")

    @patch("config.GOOGLE_CLIENT_ID", "test_google_client_id")
    def test_google_login_redirect(self):
        response = client.get("/auth/google/login", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        location = response.headers.get("location", "")
        self.assertIn("accounts.google.com/o/oauth2/v2/auth", location)
        self.assertIn("client_id=test_google_client_id", location)
        self.assertIn("response_type=code", location)
        print("  PASS: /auth/google/login redirects to Google correctly")

    @patch("config.GOOGLE_CLIENT_ID", "test_google_client_id")
    def test_google_login_has_pkce(self):
        """Verify PKCE code_challenge is present in Google OAuth URL."""
        response = client.get("/auth/google/login", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        location = response.headers.get("location", "")
        self.assertIn("code_challenge=", location)
        self.assertIn("code_challenge_method=S256", location)
        # Check pkce_verifier cookie is set
        cookies = response.cookies
        self.assertIn("pkce_verifier", dict(cookies))
        print("  PASS: /auth/google/login includes PKCE code_challenge")

    def test_google_login_fails_without_credentials(self):
        """Without GOOGLE_CLIENT_ID env var, login should return 500."""
        with patch("config.GOOGLE_CLIENT_ID", ""):
            response = client.get("/auth/google/login", follow_redirects=False)
            self.assertEqual(response.status_code, 500)
        print("  PASS: /auth/google/login rejects when credentials missing")

    def test_google_verify_missing_token(self):
        response = client.post("/auth/google/verify", json={})
        self.assertEqual(response.status_code, 400)
        print("  PASS: /auth/google/verify validates payload correctly")

if __name__ == "__main__":
    unittest.main()
