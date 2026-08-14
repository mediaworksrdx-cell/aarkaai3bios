import requests
import uuid

base_url = "http://16.170.206.243:5000"
reg_resp = requests.post(f"{base_url}/auth/register", json={
    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
    "password": "password123",
    "name": "Tester"
})
token = reg_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

query = "You have 8 balls. One is heavier. Find it in 2 weighings."
resp = requests.post(f"{base_url}/prompt", json={
    "query": query,
    "session_id": str(uuid.uuid4())
}, headers=headers)
print("Response:", repr(resp.json().get("response")))
