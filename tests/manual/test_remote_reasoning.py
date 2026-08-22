import requests
import uuid

base_url = "http://16.170.206.243:5000"
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
password = "password123"

# 1. Register
print(f"Registering user: {email}")
reg_resp = requests.post(f"{base_url}/auth/register", json={
    "email": email,
    "password": password,
    "name": "Tester"
})
print("Register Status:", reg_resp.status_code)
reg_data = reg_resp.json()
token = reg_data["access_token"]
user_id = reg_data["user_id"]
print("Token obtained.")

# 2. Send query with token
session_id = str(uuid.uuid4())
headers = {
    "Authorization": f"Bearer {token}"
}
payload = {
    "query": "A clock shows 3:15. What is the angle between the hour hand and minute hand?",
    "session_id": session_id
}

print(f"Sending query with session_id: {session_id}")
resp = requests.post(f"{base_url}/prompt", json=payload, headers=headers)
print("Response Status:", resp.status_code)
print("Response:")
print(resp.json())
