import requests

base_url = "http://16.170.206.243:5000"

# 1. Register a test user
reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

try:
    print("Registering user on remote server...")
    resp = requests.post(f"{base_url}/auth/register", json=reg_payload)
    print("Register status:", resp.status_code)
    if resp.status_code == 200:
        token_data = resp.json()
    else:
        # Try logging in if already registered
        print("Registration failed/already exists, trying login...")
        resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
        print("Login status:", resp.status_code)
        token_data = resp.json()
        
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get stats
    print("\nFetching admin stats...")
    stats_resp = requests.get(f"{base_url}/admin/stats", headers=headers)
    print("Stats Status:", stats_resp.status_code)
    print("Stats:", stats_resp.json())
    
except Exception as e:
    print("Error:", e)
