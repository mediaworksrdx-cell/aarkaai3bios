"""Test persuasion intent routing and self-checking layer."""
import requests
import json

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
print("Testing: Persuasion Intent Routing & Self-Checking Auditor")
print("============================================================")

r = requests.post(f"{BASE}/prompt", json={
    "query": "Convince me to wake up at 5 AM",
    "session_id": "test_persuasion_1",
}, headers=headers)

res = r.json()
response = res.get("response", "")
intent = res.get("intent", "")
sources = res.get("sources", [])

print(f"Detected Intent: {intent}")
print(f"Sources: {sources}")
print("--- RESPONSE ---")
print(response)
print("----------------")

# Validation: response should not list steps/instructions (like "Step 1: Set an alarm")
import re
has_steps = bool(re.search(r'\b(step\s+\d+|1\.\s+|2\.\s+|3\.\s+)', response.lower()))
print(f"Contains list of steps: {has_steps}")
print(f"PASS: {intent == 'persuasion' and not has_steps}")
