import requests
import uuid
import json

BASE_URL = "http://16.170.206.243:5000"

def run_tests():
    email = "testadmin@aarkaai.com"
    password = "supersecurepassword123"
    
    print("Logging in to remote server...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if resp.status_code != 200:
        print("Login failed, trying to register...")
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "name": "Test Admin"
        })
        
    token = resp.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    queries = [
        "How many engineering colleges are there in Tamilnadu?",
        "How many engineering colleges are there in Mangalore?"
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"\n========================================")
        print(f"QUERY {idx}: '{query}'")
        print(f"========================================")
        
        prompt_res = requests.post(f"{BASE_URL}/prompt", headers=headers, json={
            "query": query,
            "session_id": f"test_session_{uuid.uuid4().hex[:6]}"
        })
        
        if prompt_res.status_code != 200:
            print(f"Query failed: {prompt_res.status_code} - {prompt_res.text}")
            continue
            
        res_data = prompt_res.json()
        print(f"Sources used: {res_data.get('sources', [])}")
        print(f"Response:\n{res_data.get('response', '')}")

if __name__ == "__main__":
    run_tests()
