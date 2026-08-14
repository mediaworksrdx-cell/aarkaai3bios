"""Test the STREAMING endpoint for biryani recipe after confidence fallback fix."""
import requests
import time
import json

BASE = "http://localhost:5000"

# Login
login = requests.post(f"{BASE}/auth/login", json={
    "email": "visitor@aarkaai.com",
    "password": "VisitorSecurePassword123!",
    "name": "Web Visitor"
})
token = login.json().get("access_token", "")
print(f"Token: {token[:30]}...")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("=" * 60)
print("Testing: STREAMING Chicken Biryani Step-by-Step Recipe")
print("=" * 60)

start = time.time()
r = requests.post(f"{BASE}/prompt/stream", json={
    "query": "how to make chicken biryani step by step",
    "session_id": "stream_fix_1",
}, headers=headers, timeout=600, stream=True)

full_response = ""
for line in r.iter_lines():
    if line:
        text = line.decode("utf-8")
        if text.startswith("data: "):
            try:
                chunk = json.loads(text[6:])
                if chunk.get("type") == "content":
                    token_text = chunk.get("token", "")
                    full_response += token_text
                    print(token_text, end="", flush=True)
            except json.JSONDecodeError:
                pass

elapsed = time.time() - start

print(f"\n\n--- END ---")
print(f"Time: {elapsed:.1f}s")
print(f"Response length: {len(full_response)} chars")

import re
step_count = len(re.findall(r'(?:Step\s+)?\d+[\.\):]', full_response))
print(f"Numbered items found: {step_count}")
print(f"PASS: {step_count >= 5 and len(full_response) > 500}")
