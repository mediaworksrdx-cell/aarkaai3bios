"""Test that the biryani recipe fix produces complete step-by-step output."""
import requests
import time

BASE = "http://localhost:5000"

# Login to get token
login = requests.post(f"{BASE}/auth/login", json={
    "email": "visitor@aarkaai.com",
    "password": "VisitorSecurePassword123!",
    "name": "Web Visitor"
})
token = login.json().get("access_token", "")
print(f"Token: {token[:30]}...")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("=" * 60)
print("Testing: Chicken Biryani Step-by-Step Recipe")
print("=" * 60)

start = time.time()
r = requests.post(f"{BASE}/prompt", json={
    "query": "how to make chicken biryani step by step",
    "session_id": "recipe_fix_3",
}, headers=headers, timeout=300)
elapsed = time.time() - start

data = r.json()
response = data.get("response", "")
sources = data.get("sources", [])

print(f"\nHTTP Status: {r.status_code}")
print(f"Time: {elapsed:.1f}s")
print(f"Sources: {sources}")
print(f"Response length: {len(response)} chars")
print(f"\n--- FULL RESPONSE ---\n")
print(response)
print(f"\n--- END ---")

# Check quality
import re
step_count = len(re.findall(r'(?:Step\s+)?\d+[\.\):]', response))
has_ingredients = "ingredient" in response.lower() or "chicken" in response.lower()
print(f"\n--- QUALITY CHECK ---")
print(f"Has ingredients mention: {has_ingredients}")
print(f"Numbered items found: {step_count}")
print(f"Response long enough (>500 chars): {len(response) > 500}")
print(f"PASS: {has_ingredients and step_count >= 5 and len(response) > 500}")
