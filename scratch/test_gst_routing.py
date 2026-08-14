import requests
import json
import time

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    query = "What is 18% GST on 12750?"
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
