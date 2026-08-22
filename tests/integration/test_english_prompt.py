import requests

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
    
    print("\nSending 'what is 2+2' prompt request...")
    res = requests.post(
        f"{base_url}/prompt", 
        json={"query": "what is 2+2", "session_id": "default"}, 
        headers=headers
    )
    print("Status:", res.status_code)
    print("Response:")
    print(res.json().get("response"))
    
except Exception as e:
    print("Error:", e)
