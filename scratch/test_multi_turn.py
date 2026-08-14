"""Test multi-turn recipe generation via streaming to verify history capping fix."""
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

session_id = f"test_session_{int(time.time())}"

print("============================================================")
print(f"Turn 1: Ask Biryani recipe (to populate history context) on session {session_id}")
print("============================================================")

r1 = requests.post(f"{BASE}/prompt/stream", json={
    "query": "how to make chicken biryani step by step",
    "session_id": session_id,
}, headers=headers, stream=True)

resp1 = ""
for line in r1.iter_lines():
    if line:
        text = line.decode("utf-8")
        if text.startswith("data: "):
            try:
                chunk = json.loads(text[6:])
                if chunk.get("type") == "content":
                    resp1 += chunk.get("token", "")
            except:
                pass

print(f"Biryani response finished. Length: {len(resp1)} chars.")
print(resp1[:200] + "\n...\n" + resp1[-200:])

print("\n============================================================")
print("Turn 2: Ask Tikka recipe (should NOT truncate using the fixed history context)")
print("============================================================")

r2 = requests.post(f"{BASE}/prompt/stream", json={
    "query": "how to make chicken tikka step by step",
    "session_id": session_id,
}, headers=headers, stream=True)

resp2 = ""
for line in r2.iter_lines():
    if line:
        text = line.decode("utf-8")
        if text.startswith("data: "):
            try:
                chunk = json.loads(text[6:])
                if chunk.get("type") == "content":
                    token = chunk.get("token", "")
                    resp2 += token
                    print(token, end="", flush=True)
            except:
                pass

print("\n\n--- END ---")
print(f"Tikka Response length: {len(resp2)} chars")

import re
step_count = len(re.findall(r'(?:Step\s+)?\d+[\.\):]', resp2))
print(f"Numbered items found: {step_count}")
print(f"PASS: {step_count >= 4 and len(resp2) > 500}")
