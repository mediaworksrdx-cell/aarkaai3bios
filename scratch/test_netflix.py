import requests
import json

base_url = "http://16.170.206.243:5000"
query = "Design Netflix recommendation backend."

try:
    reg_res = requests.post(f"{base_url}/auth/login", json={
        "email": "testadmin@aarkaai.com",
        "password": "supersecurepassword123"
    })
    token = reg_res.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    prompt_res = requests.post(f"{base_url}/prompt", headers=headers, json={
        "query": query
    })
    print(f"Status: {prompt_res.status_code}")
    print("Response:")
    print(prompt_res.json().get("response", "").encode('ascii', 'ignore').decode('ascii'))
except Exception as e:
    print(f"Error: {e}")
