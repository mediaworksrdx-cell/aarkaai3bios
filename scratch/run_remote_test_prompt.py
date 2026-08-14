import requests

base_url = "http://localhost:5000"

print("Registering...")
try:
    reg_resp = requests.post(f"{base_url}/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Tester"
    })
    token = reg_resp.json()["access_token"]
except Exception as e:
    # Try login if already exists
    print("Already exists, logging in...")
    reg_resp = requests.post(f"{base_url}/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = reg_resp.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

print("Sending query...")
resp = requests.post(f"{base_url}/prompt", json={
    "query": "create pdf about ai agent",
    "session_id": "test"
}, headers=headers)

print("Response JSON:")
print(resp.json())
