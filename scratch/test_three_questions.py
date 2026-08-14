import requests
import json
import time
import sys

# Ensure stdout handles UTF-8 (e.g. Rupee symbol ₹)
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
    
    questions = [
        "What is 987654 × 12345?",
        "Calculate CAGR from ₹10,000 to ₹25,000 in 5 years.",
        "What is 18% GST on ₹12,750?"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n--- Question {i}: {q} ---")
        start_time = time.time()
        res = requests.post(
            f"{base_url}/prompt", 
            json={"query": q, "session_id": f"session_{i}_{int(time.time())}"}, 
            headers=headers
        )
        duration = time.time() - start_time
        print(f"Status: {res.status_code} (took {duration:.2f}s)")
        if res.status_code == 200:
            resp_data = res.json()
            print("Response:")
            print(resp_data.get("response"))
        else:
            print("Failed:", res.text)
            
except Exception as e:
    print("Error:", e)
