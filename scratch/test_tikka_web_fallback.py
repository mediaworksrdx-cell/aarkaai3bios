"""Test streaming endpoint with chicken tikka query to verify web search fallback."""
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
print("Testing: STREAMING Chicken Tikka with RAG Bypass -> Web Fallback")
print("============================================================")

r = requests.post(f"{BASE}/prompt/stream", json={
    "query": "how to make chicken tikka step by step",
    "session_id": "test_tikka_fallback_1",
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

import re
step_count = len(re.findall(r'(?:Step\s+)?\d+[\.\):]', resp))
print(f"Numbered items found: {step_count}")
print(f"PASS: {step_count >= 5 and len(resp) > 500}")
