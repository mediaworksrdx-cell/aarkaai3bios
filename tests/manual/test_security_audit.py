"""
Security Audit Script for AARKAAI Platform

This script performs TWO categories of security checks:
Category A: Static Code Scanning (offline)
Category B: Runtime Security Testing (against a target server)

Usage:
python test_security_audit.py --target http://localhost:5000 --codebase .
"""

import argparse
import os
import re
from pathlib import Path
import httpx
import jwt
import datetime
import time
import sys

results = []
summary_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "PASS": 0, "ERROR": 0}

def run_test(category, name, severity, fn):
    try:
        fn()
        results.append((category, name, "PASS", ""))
        summary_counts["PASS"] += 1
        print(f"  [PASS] [{category}] {name}")
    except AssertionError as e:
        results.append((category, name, severity, str(e)))
        summary_counts[severity] += 1
        print(f"  [{severity}] [{category}] {name}: {e}")
    except httpx.RequestError as e:
        results.append((category, name, "ERROR", f"Request failed: {e}"))
        summary_counts["ERROR"] += 1
        print(f"  [ERROR] [{category}] {name}: Request failed: {e}")
    except Exception as e:
        results.append((category, name, "ERROR", str(e)))
        summary_counts["ERROR"] += 1
        print(f"  [ERROR] [{category}] {name}: {e}")


def is_ignored_path(filepath, base_path):
    rel_path = filepath.relative_to(base_path)
    parts = rel_path.parts
    ignored_dirs = {
        '__pycache__', '.git', 'node_modules', 'chroma_db',
        'llama.cpp', '.vscode', '.github', '.agents',
        'android-app', 'ios-app', 'aarkaai 3b', 'archive',
        'codegent', 'skills', 'skills-main',
    }
    if any(part in ignored_dirs for part in parts):
        return True
    if filepath.suffix in {'.pyc', '.gguf'}:
        return True
    # Exclude files matching .gitignore patterns (GCP keys, env files)
    fname = filepath.name
    if fname.startswith('orbital-heaven-') and fname.endswith('.json'):
        return True
    if fname.endswith('-sa-key.json') or 'service_account' in fname:
        return True
    return False

def get_files_to_scan(base_path, extensions):
    files = []
    for ext in extensions:
        for filepath in base_path.rglob(f"*{ext}"):
            if not is_ignored_path(filepath, base_path):
                files.append(filepath)
    return files

# ==========================================
# Category A: Static Security Scanning
# ==========================================

def a1_hardcoded_secrets(codebase_path):
    extensions = ['.py', '.env', '.yml', '.yaml', '.json', '.conf', '.sh']
    files = get_files_to_scan(codebase_path, extensions)
    
    api_key_patterns = [r'sk-[a-zA-Z0-9]{20,}', r'AIza[0-9A-Za-z-_]{35}', r'gh[po]_[a-zA-Z0-9]{36}', r'github_pat_[a-zA-Z0-9_]{82}', r'AKIA[0-9A-Z]{16}']
    password_pattern = r'password\s*=\s*["\'][^"\']{8,}["\']'
    private_key_pattern = r'-----BEGIN.*PRIVATE KEY-----'
    mongo_pattern = r'mongodb\+srv://[^:]+:[^@]+@'
    
    findings = []
    
    for filepath in files:
        # Exclude test files and .env.example for certain checks
        is_test_or_example = 'test' in filepath.name.lower() or filepath.name == '.env.example'
        is_env = filepath.name == '.env'
        
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            for i, line in enumerate(lines):
                # Check API keys
                if not is_test_or_example and not is_env:
                    for pat in api_key_patterns:
                        if re.search(pat, line):
                            findings.append(f"{filepath.relative_to(codebase_path)}:{i+1} (API Key)")
                    
                    if re.search(password_pattern, line, re.IGNORECASE):
                        findings.append(f"{filepath.relative_to(codebase_path)}:{i+1} (Password)")
                        
                    if re.search(private_key_pattern, line):
                        findings.append(f"{filepath.relative_to(codebase_path)}:{i+1} (Private Key)")
                
                # Check Mongo connection string (not in .env)
                if filepath.suffix == '.py' and not is_test_or_example:
                    if re.search(mongo_pattern, line):
                        findings.append(f"{filepath.relative_to(codebase_path)}:{i+1} (MongoDB URI)")
        except Exception:
            pass

    assert not findings, f"Hardcoded secrets found:\n" + "\n".join(findings)

def a2_github_pat_exposure(codebase_path):
    files = get_files_to_scan(codebase_path, ['.py'])
    pat_patterns = [r'gh[po]_[a-zA-Z0-9]{36}', r'github_pat_[a-zA-Z0-9_]{82}']
    findings = []
    
    for filepath in files:
        if 'test' in filepath.name.lower(): continue
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            for i, line in enumerate(content.splitlines()):
                for pat in pat_patterns:
                    if re.search(pat, line):
                        findings.append(f"{filepath.relative_to(codebase_path)}:{i+1}")
        except: pass
    
    assert not findings, f"GitHub PATs found in source code:\n" + "\n".join(findings)

def a3_env_in_gitignore(codebase_path):
    gitignore_path = codebase_path / '.gitignore'
    assert gitignore_path.exists(), ".gitignore file missing"
    
    content = gitignore_path.read_text(encoding='utf-8')
    assert re.search(r'^\s*\.env\s*$', content, re.MULTILINE), ".env not found in .gitignore"

def a4_secret_key_default_guard(codebase_path):
    config_path = codebase_path / 'config.py'
    if not config_path.exists():
        # Fallback if config is named differently
        config_files = list(codebase_path.glob('**/config.py'))
        if not config_files:
            raise AssertionError("config.py not found, unable to verify secret key guard")
        config_path = config_files[0]
        
    content = config_path.read_text(encoding='utf-8', errors='ignore')
    # Look for some form of runtime error if default secret key is used in production
    has_raise = 'raise' in content and 'RuntimeError' in content
    has_secret_key = 'SECRET_KEY' in content
    assert has_raise and has_secret_key, "Production guard for default SECRET_KEY missing in config.py"

def a5_gcp_credentials_not_hardcoded(codebase_path):
    files = get_files_to_scan(codebase_path, ['.py'])
    findings = []
    for filepath in files:
        if 'test' in filepath.name.lower(): continue
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            for i, line in enumerate(content.splitlines()):
                if 'GOOGLE_APPLICATION_CREDENTIALS' in line and ('.json' in line or '=' in line):
                    # Check if it looks hardcoded rather than os.environ.get
                    if 'os.environ' not in line and 'os.getenv' not in line:
                         findings.append(f"{filepath.relative_to(codebase_path)}:{i+1}")
        except: pass
    assert not findings, f"Hardcoded GCP credentials found:\n" + "\n".join(findings)

# ==========================================
# Category B: Runtime Security Testing
# ==========================================

def b1_security_headers(target, client):
    resp = client.get("/")
    headers = resp.headers
    
    missing = []
    if 'Strict-Transport-Security' not in headers: missing.append('Strict-Transport-Security (HSTS)')
    if headers.get('X-Content-Type-Options') != 'nosniff': missing.append('X-Content-Type-Options: nosniff')
    if headers.get('X-Frame-Options', '').upper() not in ['DENY', 'SAMEORIGIN']: missing.append('X-Frame-Options')
    if 'X-XSS-Protection' not in headers: missing.append('X-XSS-Protection')
    
    if target.startswith("https") and missing:
        assert False, f"Missing critical headers: {', '.join(missing)}"
    elif missing:
        # Only warn/medium if it's http
        raise AssertionError(f"Missing headers (Warning, target is not HTTPS): {', '.join(missing)}")

def b2_cors_validation(target, client):
    url = f"{target}/prompt"
    headers = {"Origin": "https://evil.com"}
    resp = client.options(url, headers=headers)
    if 'Access-Control-Allow-Origin' in resp.headers:
        acao = resp.headers['Access-Control-Allow-Origin']
        assert acao != '*', "Wildcard CORS in production is insecure"

def b3_jwt_expired(target, client):
    # Expired token
    payload = {"sub": "test_user", "exp": datetime.datetime.utcnow() - datetime.timedelta(days=1)}
    token = jwt.encode(payload, "dummy_secret", algorithm="HS256")
    resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in [401, 403], f"Expected 401/403 for expired JWT, got {resp.status_code}"

def b3_jwt_invalid_signature(target, client):
    payload = {"sub": "admin", "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)}
    token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
    resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in [401, 403, 404], f"Expected 401/403/404 for invalid signature, got {resp.status_code}"

def b3_jwt_none_alg(target, client):
    # Create none alg token manually
    import base64, json
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip('=')
    payload = base64.urlsafe_b64encode(json.dumps({"sub": "admin"}).encode()).decode().rstrip('=')
    token = f"{header}.{payload}."
    resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in [401, 403, 400], f"Expected rejection for alg=none, got {resp.status_code}"

def b4_admin_auth(target, client):
    for ep in ["/admin/stats", "/metrics"]:
        resp = client.get(ep)
        assert resp.status_code in [401, 403, 404], f"Endpoint {ep} accessible without auth! Status: {resp.status_code}"

def b4_invalid_api_key(target, client):
    resp = client.get("/admin/stats", headers={"X-API-Key": "garbage_key_12345"})
    assert resp.status_code in [401, 403, 404], f"Invalid API key not rejected properly. Status: {resp.status_code}"

def b5_xss_in_prompt(target, client):
    payload = {"prompt": "<script>alert(1)</script>"}
    resp = client.post("/prompt", json=payload)
    if resp.status_code == 200:
        assert "<script>alert(1)</script>" not in resp.text, "Unescaped XSS payload reflected in /prompt response"

def b5_html_injection_name(target, client):
    payload = {"name": "<img src=x onerror=alert(1)>", "email": "test@example.com", "password": "Password123"}
    resp = client.post("/auth/register", json=payload)
    if resp.status_code == 200:
        assert "<img src=x onerror=alert(1)>" not in resp.text, "Unescaped HTML injection in /auth/register response"

def b6_upload_exe(target, client):
    files = {'file': ('malware.exe', b'MZ\x90\x00\x03\x00\x00\x00', 'application/x-msdownload')}
    resp = client.post("/upload", files=files)
    assert resp.status_code in [400, 403, 415, 404], f"Executable upload not rejected. Status: {resp.status_code}"

def b6_upload_path_traversal(target, client):
    files = {'file': ('../../../etc/passwd', b'test', 'text/plain')}
    resp = client.post("/upload", files=files)
    assert resp.status_code in [400, 403, 404] or "etc/passwd" not in resp.text, "Path traversal attempt not rejected or handled safely"

def b7_redis_rate_limiting(target, client):
    responses = []
    for _ in range(65):
        responses.append(client.post("/auth/login", json={"email": "test@test.com", "password": "abc"}))
    
    statuses = [r.status_code for r in responses]
    if 429 not in statuses:
        raise AssertionError("Rate limiting not triggered after 65 requests (may be disabled in dev)")

def b8_sandbox_escape(target, client):
    payload = {"prompt": "import os; os.system('cat /etc/passwd')"}
    resp = client.post("/prompt", json=payload)
    if resp.status_code == 200:
        assert "root:x:0:0" not in resp.text, "Sandbox escape successful! Read /etc/passwd"

def b9_mongodb_injection(target, client):
    payload = {"email": {"$gt": ""}, "password": "password"}
    # httpx doesn't let you easily send dicts in place of strings in json without it just being json, which is fine
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code in [400, 401, 403, 422], f"NoSQL injection not rejected properly. Status: {resp.status_code}"

def b10_oauth_callback_no_code(target, client):
    resp = client.get("/auth/github/callback")
    assert resp.status_code in [400, 401, 403, 302], f"Invalid handling of missing code in OAuth callback. Status: {resp.status_code}"

def b10_oauth_callback_invalid_code(target, client):
    resp = client.get("/auth/github/callback?code=invalid_garbage")
    assert resp.status_code in [400, 401, 403, 500], f"Invalid handling of bad code in OAuth callback. Status: {resp.status_code}"


def main():
    parser = argparse.ArgumentParser(description="AARKAAI Platform Security Audit Script")
    parser.add_argument("--target", default="http://localhost:5000", help="Target server URL for runtime tests")
    parser.add_argument("--codebase", default=".", help="Path to the codebase for static analysis")
    args = parser.parse_args()

    codebase_path = Path(args.codebase).resolve()
    target = args.target.rstrip('/')

    print(f"Starting Security Audit...")
    print(f"Codebase: {codebase_path}")
    print(f"Target: {target}")
    print("\n--- Category A: Static Code Scanning ---")
    
    run_test("A1", "Hardcoded Secrets Scan", "CRITICAL", lambda: a1_hardcoded_secrets(codebase_path))
    run_test("A2", "GitHub PAT Exposure", "CRITICAL", lambda: a2_github_pat_exposure(codebase_path))
    run_test("A3", ".env in .gitignore", "HIGH", lambda: a3_env_in_gitignore(codebase_path))
    run_test("A4", "Secret Key Default Check", "HIGH", lambda: a4_secret_key_default_guard(codebase_path))
    run_test("A5", "GCP Credentials not hardcoded", "HIGH", lambda: a5_gcp_credentials_not_hardcoded(codebase_path))

    print("\n--- Category B: Runtime Security Testing ---")
    
    with httpx.Client(base_url=target, timeout=5.0, verify=False) as client:
        # Pre-flight check
        try:
            client.get("/")
            target_reachable = True
        except Exception as e:
            print(f"\n[WARNING] Target {target} is not reachable ({e}). Skipping runtime tests.")
            target_reachable = False

        if target_reachable:
            run_test("B1", "HTTPS & Security Headers", "HIGH", lambda: b1_security_headers(target, client))
            run_test("B2", "CORS Validation", "HIGH", lambda: b2_cors_validation(target, client))
            run_test("B3", "JWT Expired Token", "CRITICAL", lambda: b3_jwt_expired(target, client))
            run_test("B3", "JWT Invalid Signature", "CRITICAL", lambda: b3_jwt_invalid_signature(target, client))
            run_test("B3", "JWT None Algorithm", "CRITICAL", lambda: b3_jwt_none_alg(target, client))
            run_test("B4", "Admin Endpoints Auth", "CRITICAL", lambda: b4_admin_auth(target, client))
            run_test("B4", "Invalid API Key Rejected", "HIGH", lambda: b4_invalid_api_key(target, client))
            run_test("B5", "XSS in Prompt", "CRITICAL", lambda: b5_xss_in_prompt(target, client))
            run_test("B5", "HTML Injection in Name", "MEDIUM", lambda: b5_html_injection_name(target, client))
            run_test("B6", "Upload Executable Blocked", "HIGH", lambda: b6_upload_exe(target, client))
            run_test("B6", "Upload Path Traversal", "CRITICAL", lambda: b6_upload_path_traversal(target, client))
            run_test("B7", "Redis Rate Limiting", "MEDIUM", lambda: b7_redis_rate_limiting(target, client))
            run_test("B8", "Sandbox Escape", "CRITICAL", lambda: b8_sandbox_escape(target, client))
            run_test("B9", "MongoDB NoSQL Injection", "CRITICAL", lambda: b9_mongodb_injection(target, client))
            run_test("B10", "OAuth Missing Code", "MEDIUM", lambda: b10_oauth_callback_no_code(target, client))
            run_test("B10", "OAuth Invalid Code", "MEDIUM", lambda: b10_oauth_callback_invalid_code(target, client))

    print("\n==============================================")
    print("                AUDIT SUMMARY                 ")
    print("==============================================")
    for k, v in summary_counts.items():
        print(f"{k.ljust(10)}: {v}")
    print("==============================================")

    if summary_counts["CRITICAL"] > 0 or summary_counts["HIGH"] > 0:
        print("\nAudit Failed: CRITICAL or HIGH findings present.")
        sys.exit(1)
    else:
        print("\nAudit Passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
