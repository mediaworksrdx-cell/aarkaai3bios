import requests
import uuid
import json

BASE_URL = "http://16.170.206.243:5000"

def test_remote():
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    password = "TestPassword123!"
    
    print("1. Registering user...")
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "name": "QA Tester"
    })
    
    if reg_res.status_code != 200:
        print(f"Registration failed: {reg_res.text}")
        return
        
    reg_data = reg_res.json()
    token = reg_data["access_token"]
    print("Registration successful, token acquired.")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n2. Querying: 'what is the price of gold'...")
    prompt_res = requests.post(f"{BASE_URL}/prompt", headers=headers, json={
        "query": "what is the price of gold"
    })
    
    if prompt_res.status_code != 200:
        print(f"Prompt query failed: {prompt_res.status_code} - {prompt_res.text}")
        return
        
    print("\n=== Live API Response ===")
    print(json.dumps(prompt_res.json(), indent=2))

if __name__ == "__main__":
    test_remote()
