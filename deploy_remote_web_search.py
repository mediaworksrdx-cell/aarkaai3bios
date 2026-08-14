import requests

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

with open("modules/web_search.py", "r", encoding="utf-8") as f:
    local_code = f.read()

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Task query to write our updated code to modules/web_search.py on the remote server
    task_query = f"""Please run a python script to overwrite the content of modules/web_search.py on the remote server with the following code. Write it carefully, ensuring no lines are truncated.

```python
{local_code}
```
"""
    
    print("\nSending prompt request to update file on remote server...")
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
