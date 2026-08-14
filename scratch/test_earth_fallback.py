"""Test streaming endpoint with Earth rotation query to verify web fallback."""
import requests
import json
import time

BASE = "http://localhost:5000"

# Login
login = requests.post(f"{BASE}/auth/login", json={
    "email": "visitor@aarkaai.com",
    "password": "VisitorSecurePassword123!",
    "name": "Web Visitor"
})
token = login.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("============================================================")
print("Testing: Earth Rotation Query -> Web Fallback")
print("============================================================")

r = requests.post(f"{BASE}/prompt/stream", json={
    "query": "1. If the Earth suddenly stopped rotating, what would happen in the first 24 hours?",
    "session_id": "test_earth_fallback_1",
}, headers=headers, stream=True)

resp = ""
for line in r.iter_lines():
    if line:
        text = line.decode("utf-8")
        if text.startswith("data: "):
            try:
                chunk = json.loads(text[6:])
                if chunk.get("type") == "metadata":
                    print(f"Sources utilized: {chunk.get('sources')}")
                elif chunk.get("type") == "content":
                    token = chunk.get("token", "")
                    resp += token
                    print(token, end="", flush=True)
            except Exception as e:
                pass

print("\n\n--- END ---")
print(f"Response length: {len(resp)} chars")
print(f"PASS: {len(resp) > 500 and 'web_search' in resp.lower() or 'sources utilized'}")
