import requests
import uuid

base_url = "http://16.170.206.243:5000"
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
password = "password123"

# 1. Register
print(f"Registering user: {email} on {base_url}...")
reg_resp = requests.post(f"{base_url}/auth/register", json={
    "email": email,
    "password": password,
    "name": "Tester"
})
print("Register Status:", reg_resp.status_code)
if reg_resp.status_code != 200:
    print("Registration failed:", reg_resp.text)
    # Try logging in directly if user already exists
    exit(1)

reg_data = reg_resp.json()
token = reg_data["access_token"]
user_id = reg_data["user_id"]
print("Token obtained successfully.")

# 2. Send query with token
session_id = str(uuid.uuid4())
headers = {
    "Authorization": f"Bearer {token}"
}
query = "You have 5 billion log entries. Need to find the top 100 most frequent IP addresses. Only 2 GB RAM available. How would you solve it?"
payload = {
    "query": query,
    "session_id": session_id
}

print(f"\nSending query to remote server:\n{query}")
resp = requests.post(f"{base_url}/prompt", json=payload, headers=headers)
print("\nResponse Status:", resp.status_code)
if resp.status_code == 200:
    resp_data = resp.json()
    print("\n--- REMOTE PIPELINE RESPONSE ---")
    print("Sources Used:", resp_data.get("sources"))
    print("Detected Language:", resp_data.get("detected_language"))
    print("Processing Time:", resp_data.get("processing_time"))
    print("\nResponse:")
    print(resp_data.get("response"))
    print("--------------------------------")
else:
    print("Failed to get response from remote:", resp.text)
