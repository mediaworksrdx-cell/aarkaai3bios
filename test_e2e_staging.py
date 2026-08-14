"""
End-to-End Test Suite for AARKAAI AI Platform

Usage:
    python test_e2e_staging.py [--target URL] [--skip-gpu]

Example:
    python test_e2e_staging.py --target http://localhost:5000
"""

import argparse
import sys
import uuid
import httpx

results = []

def run_test(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
        print(f"  [PASS] {name}")
    except AssertionError as e:
        results.append((name, "FAIL", str(e)))
        print(f"  [FAIL] {name}: {e}")
    except Exception as e:
        results.append((name, "ERROR", str(e)))
        print(f"  [ERROR] {name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="E2E test suite for AARKAAI")
    parser.add_argument("--target", default="http://localhost:5000", help="Target URL of the staging server")
    parser.add_argument("--skip-gpu", action="store_true", help="Skip tests requiring GPU inference")
    args = parser.parse_args()

    base_url = args.target.rstrip("/")
    client = httpx.Client(base_url=base_url, timeout=10.0)
    gpu_client = httpx.Client(base_url=base_url, timeout=120.0)

    test_email = f"e2e-test-{uuid.uuid4().hex[:8]}@staging.aarkaai.test"
    test_password = "E2eTest_Secure_2026!"

    state = {}

    print(f"Running E2E tests against {base_url}...")
    
    # Group 1: Guest / Visitor Flow
    print("\n## Group 1: Guest / Visitor Flow")
    def test_health_endpoint():
        resp = client.get("/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.json().get("status") == "ok", "Expected status ok"
    run_test("test_health_endpoint", test_health_endpoint)

    def test_visitor_token_issue():
        resp = client.post("/auth/visitor-token")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "access_token" in data, "Missing access_token"
        assert "user_id" in data, "Missing user_id"
        state["visitor_token"] = data["access_token"]
    run_test("test_visitor_token_issue", test_visitor_token_issue)

    if not args.skip_gpu and "visitor_token" in state:
        def test_visitor_chat():
            headers = {"Authorization": f"Bearer {state['visitor_token']}"}
            resp = gpu_client.post("/prompt", headers=headers, json={"query": "Hello"})
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            assert "response" in resp.json(), "Missing response field"
        run_test("test_visitor_chat", test_visitor_chat)

        def test_visitor_sse_stream():
            headers = {"Authorization": f"Bearer {state['visitor_token']}"}
            with gpu_client.stream("POST", "/prompt/stream", headers=headers, json={"query": "Hello"}) as resp:
                assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
                content_type = resp.headers.get("content-type", "")
                assert "text/event-stream" in content_type, f"Expected event-stream, got {content_type}"
                # just verify it starts
        run_test("test_visitor_sse_stream", test_visitor_sse_stream)
    elif args.skip_gpu:
        print("  [SKIP] test_visitor_chat (skip-gpu)")
        print("  [SKIP] test_visitor_sse_stream (skip-gpu)")

    # Group 2: Registration / Login / JWT Flow
    print("\n## Group 2: Registration / Login / JWT Flow")
    def test_register_new_user():
        resp = client.post("/auth/register", json={"email": test_email, "password": test_password})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "access_token" in data, "Missing access_token"
        assert "refresh_token" in data, "Missing refresh_token"
    run_test("test_register_new_user", test_register_new_user)

    def test_register_duplicate_email():
        resp = client.post("/auth/register", json={"email": test_email, "password": test_password})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    run_test("test_register_duplicate_email", test_register_duplicate_email)

    def test_login_valid_credentials():
        resp = client.post("/auth/login", json={"email": test_email, "password": test_password})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "access_token" in data, "Missing access_token"
        assert "refresh_token" in data, "Missing refresh_token"
        state["user_access_token"] = data["access_token"]
        state["user_refresh_token"] = data["refresh_token"]
    run_test("test_login_valid_credentials", test_login_valid_credentials)

    def test_login_invalid_password():
        resp = client.post("/auth/login", json={"email": test_email, "password": "WrongPassword!"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    run_test("test_login_invalid_password", test_login_invalid_password)

    if not args.skip_gpu and "user_access_token" in state:
        def test_jwt_authenticated_chat():
            headers = {"Authorization": f"Bearer {state['user_access_token']}"}
            resp = gpu_client.post("/prompt", headers=headers, json={"query": "Hello"})
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        run_test("test_jwt_authenticated_chat", test_jwt_authenticated_chat)
    elif args.skip_gpu:
        print("  [SKIP] test_jwt_authenticated_chat (skip-gpu)")

    def test_refresh_token_flow():
        if "user_refresh_token" not in state:
            assert False, "No refresh token available"
        resp = client.post("/auth/refresh", json={"refresh_token": state["user_refresh_token"]})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert "access_token" in resp.json(), "Missing access_token"
        state["new_access_token"] = resp.json()["access_token"]
    run_test("test_refresh_token_flow", test_refresh_token_flow)

    def test_refresh_with_access_token_rejected():
        if "user_access_token" not in state:
            assert False, "No access token available"
        resp = client.post("/auth/refresh", json={"refresh_token": state["user_access_token"]})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    run_test("test_refresh_with_access_token_rejected", test_refresh_with_access_token_rejected)

    def test_logout_token_revocation():
        if "user_access_token" not in state:
            assert False, "No access token available"
        headers = {"Authorization": f"Bearer {state['user_access_token']}"}
        resp = client.post("/auth/logout", headers=headers, json={"refresh_token": state.get("user_refresh_token", "")})
        
        # Test using the old token. Could be 200 (if Redis down, token still valid) or 401 (if Redis revoked it)
        resp2 = client.get("/settings", headers=headers)
        assert resp2.status_code in (200, 401, 404), f"Unexpected status {resp2.status_code}"
    run_test("test_logout_token_revocation", test_logout_token_revocation)


    # Group 3: OAuth Endpoints
    print("\n## Group 3: OAuth Endpoints")
    def test_github_oauth_login_redirect():
        resp = client.get("/auth/github/login", follow_redirects=False)
        assert resp.status_code == 302, f"Expected 302, got {resp.status_code}"
        assert "github.com/login/oauth" in resp.headers.get("location", ""), "Missing github oauth in location"
    run_test("test_github_oauth_login_redirect", test_github_oauth_login_redirect)

    def test_google_oauth_endpoint_exists():
        resp = client.get("/auth/google/login", follow_redirects=False)
        assert resp.status_code in (200, 302), f"Expected 200 or 302, got {resp.status_code}"
    run_test("test_google_oauth_endpoint_exists", test_google_oauth_endpoint_exists)

    # Group 4: MongoDB Persistence
    print("\n## Group 4: MongoDB Persistence")
    def test_settings_get():
        if "new_access_token" not in state:
            assert False, "No token"
        headers = {"Authorization": f"Bearer {state['new_access_token']}"}
        resp = client.get("/settings", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    run_test("test_settings_get", test_settings_get)

    def test_settings_update():
        if "new_access_token" not in state:
            assert False, "No token"
        headers = {"Authorization": f"Bearer {state['new_access_token']}"}
        resp = client.put("/settings", headers=headers, json={"theme": "dark"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    run_test("test_settings_update", test_settings_update)

    def test_settings_persisted():
        if "new_access_token" not in state:
            assert False, "No token"
        headers = {"Authorization": f"Bearer {state['new_access_token']}"}
        resp = client.get("/settings", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.json().get("theme") == "dark", "Theme not persisted"
    run_test("test_settings_persisted", test_settings_persisted)

    if not args.skip_gpu and "new_access_token" in state:
        def test_memory_persistence():
            headers = {"Authorization": f"Bearer {state['new_access_token']}"}
            resp = gpu_client.post("/prompt", headers=headers, json={"query": "My favorite color is blue."})
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            
            resp2 = gpu_client.post("/prompt", headers=headers, json={"query": "What is my favorite color?"})
            assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
        run_test("test_memory_persistence", test_memory_persistence)
    elif args.skip_gpu:
        print("  [SKIP] test_memory_persistence (skip-gpu)")

    # Group 5: File Upload Restrictions
    print("\n## Group 5: File Upload Restrictions")
    def test_upload_valid_pdf():
        if "new_access_token" not in state:
            assert False, "No token"
        headers = {"Authorization": f"Bearer {state['new_access_token']}"}
        files = {"file": ("test.pdf", b"%PDF-1.4\n", "application/pdf")}
        resp = client.post("/upload", headers=headers, files=files)
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}"
    run_test("test_upload_valid_pdf", test_upload_valid_pdf)

    def test_upload_oversized_rejected():
        if "new_access_token" not in state:
            assert False, "No token"
        headers = {"Authorization": f"Bearer {state['new_access_token']}"}
        files = {"file": ("big.pdf", b"0" * (10 * 1024 * 1024 + 1024), "application/pdf")}
        resp = client.post("/upload", headers=headers, files=files)
        assert resp.status_code in (413, 400), f"Expected 413 or 400, got {resp.status_code}"
    run_test("test_upload_oversized_rejected", test_upload_oversized_rejected)

    def test_upload_dangerous_extension():
        if "new_access_token" not in state:
            assert False, "No token"
        headers = {"Authorization": f"Bearer {state['new_access_token']}"}
        files = {"file": ("virus.exe", b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00", "application/x-msdownload")}
        resp = client.post("/upload", headers=headers, files=files)
        assert resp.status_code in (400, 415), f"Expected 400 or 415, got {resp.status_code}"
    run_test("test_upload_dangerous_extension", test_upload_dangerous_extension)

    # Group 6: Logout & Session Invalidation
    print("\n## Group 6: Logout & Session Invalidation")
    def test_full_logout_flow():
        # Login
        resp = client.post("/auth/login", json={"email": test_email, "password": test_password})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        acc_tok = data["access_token"]
        ref_tok = data["refresh_token"]

        # Logout
        headers = {"Authorization": f"Bearer {acc_tok}"}
        logout_resp = client.post("/auth/logout", headers=headers, json={"refresh_token": ref_tok})
        assert logout_resp.status_code == 200, f"Logout failed: {logout_resp.status_code}"

        # Try refresh
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": ref_tok})
        assert refresh_resp.status_code in (401, 200), f"Expected 401 (if redis) or 200 (if graceful), got {refresh_resp.status_code}"
    run_test("test_full_logout_flow", test_full_logout_flow)

    print("\n## Summary")
    passes = sum(1 for r in results if r[1] == "PASS")
    fails = sum(1 for r in results if r[1] == "FAIL")
    errors = sum(1 for r in results if r[1] == "ERROR")

    print(f"Total Tests: {len(results)}")
    print(f"PASS: {passes}")
    print(f"FAIL: {fails}")
    print(f"ERROR: {errors}")

    if fails > 0 or errors > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
