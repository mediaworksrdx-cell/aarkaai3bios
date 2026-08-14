import requests
import json
import time
import sys

# Ensure stdout handles UTF-8
sys.stdout.reconfigure(encoding='utf-8')

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
    
    query = "1000 AED to INR"
    print(f"\nSending prompt request: '{query}'...")
    start_time = time.time()
    res = requests.post(
        f"{base_url}/prompt", 
        json={"query": query, "session_id": f"session_fuzzy_{int(time.time())}"}, 
        headers=headers
    )
    duration = time.time() - start_time
    print(f"Status: {res.status_code} (took {duration:.2f}s)")
    if res.status_code == 200:
        print("Response:")
        print(res.json().get("response"))
    else:
        print("Failed:", res.text)
        
except Exception as e:
    print("Error:", e)
