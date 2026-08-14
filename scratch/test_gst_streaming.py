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
    print(f"\nSending streaming prompt request: '{query}'...")
    res = requests.post(
        f"{base_url}/prompt/stream", 
        json={"query": query, "session_id": "default"}, 
        headers=headers,
        stream=True
    )
    print("Status:", res.status_code)
    for line in res.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[6:])
                print("CHUNK:", data)
                
except Exception as e:
    print("Error:", e)
