import requests
import sys

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

code_to_run = """
import os
import sys
import subprocess

print("=== REMOTE SERVER ENVIRONMENT ===")
print("CWD:", os.getcwd())
print("Python Executable:", sys.executable)
print("Files in CWD:", os.listdir("."))

print("\n=== SYSTEM AND PYTHON PATH ===")
print("PATH:", os.environ.get("PATH"))
print("HF_TOKEN in env:", "HF_TOKEN" in os.environ)

print("\n=== TRYING TO QUERY HUGGINGFACE PUBLIC API FOR rthshr/aarkaa-3b ===")
try:
    import urllib.request
    import json
    url = "https://huggingface.co/api/models/rthshr/aarkaa-3b"
    req = urllib.request.Request(url)
    if "HF_TOKEN" in os.environ:
        req.add_header("Authorization", f"Bearer {os.environ['HF_TOKEN']}")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("HF API success!")
        print("Model ID:", data.get("modelId"))
        print("Files:")
        for f in data.get("siblings", []):
            print("  -", f.get("rfilename"))
except Exception as e:
    print("HF API error:", e)
"""

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    task_query = f"""Please run this Python code on the remote server and print the exact stdout/stderr output:
```python
{code_to_run}
```
"""
    
    print("\nSending prompt request to execute code...")
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
