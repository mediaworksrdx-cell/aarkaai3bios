import requests
import sys

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

# Query to compile the Chennai Tech Startups premium report
task_query = 'Please compile a premium PDF report on "Chennai Tech Startups".'

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    print("Login Response Status:", resp.status_code)
    token = resp.json().get("access_token")
    if not token:
        print("Registering first...")
        reg_resp = requests.post(f"{base_url}/auth/register", json=reg_payload)
        token = reg_resp.json()["access_token"]
        
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nSending prompt request to execute command...")
    res = requests.post(
        f"{base_url}/prompt", 
        json={"query": task_query, "session_id": "default"}, 
        headers=headers
    )
    print("Status:", res.status_code)
    print("Response JSON:")
    print(res.json()["response"])
    
except Exception as e:
    print("Error:", e)
