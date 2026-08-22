import time
import requests

BASE = "http://localhost:5000"

# Login to get token
login = requests.post(f"{BASE}/auth/login", json={
    "email": "visitor@aarkaai.com",
    "password": "VisitorSecurePassword123!",
    "name": "Web Visitor"
})
token = login.json().get("access_token", "")
print(f"Token: {token[:30]}...")

# Send prompt
start = time.time()
resp = requests.post(f"{BASE}/prompt", json={
    "query": "how to make briyani",
    "session_id": "test-session"
}, headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}, timeout=120)
elapsed = time.time() - start

print(f"Status: {resp.status_code}")
print(f"Time: {elapsed:.1f}s")
print(f"Response data:")
res_json = resp.json()
print("Response text:", res_json.get("response"))
print("Sources:", res_json.get("sources"))
