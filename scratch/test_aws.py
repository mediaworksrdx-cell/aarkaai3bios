import requests
import uuid
import json

base_url = "http://16.170.206.243:5000"

query = "Design a distributed URL shortening service like TinyURL. It needs to handle 100M new URLs per day. Discuss storage, cache, core algorithm, bottlenecks, and multi-region replication."

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
    print("Response text:")
    print(prompt_res.text.encode('ascii', 'ignore').decode('ascii'))
except Exception as e:
    print(f"Error: {e}")
