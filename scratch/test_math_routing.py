import requests
import json
import time

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

# Wait for backend to reload
print("Waiting 15 seconds for backend to start up...")
time.sleep(15)

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    query = "What is 56789 * 98765?"
    print(f"\nSending prompt request: '{query}'...")
    res = requests.post(
        f"{base_url}/prompt", 
        json={"query": query, "session_id": "default"}, 
        headers=headers
    )
    print("Status:", res.status_code)
    print("Response JSON:")
    print(json.dumps(res.json(), indent=2))
    
except Exception as e:
    print("Error:", e)
