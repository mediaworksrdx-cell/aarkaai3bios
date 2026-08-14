"""Quick test for the /strategy endpoint."""
import json
import requests

BASE = "http://16.170.206.243:5000"

# 1. Get a token
r = requests.post(f"{BASE}/auth/login", json={"email": "darvin@example.com", "password": "test123"})
if r.status_code != 200:
    r = requests.post(f"{BASE}/auth/register", json={"email": "darvin@example.com", "password": "test123", "name": "Darvin"})
token = r.json().get("access_token", "")
print(f"Token: {token[:20]}...")

# 2. Hit the /strategy endpoint for SBI
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
r2 = requests.post(f"{BASE}/strategy", json={"symbol": "SBIN.NS", "risk_reward": 5.0}, headers=headers, timeout=60)
print(f"\nStatus: {r2.status_code}")
data = r2.json()
output = json.dumps(data, indent=2, ensure_ascii=True)
print(output)
