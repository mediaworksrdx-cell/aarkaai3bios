import requests

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

code_to_run = """
import os
import sqlite3

print("=== REMOTE FILES UNDER skills/ ===")
for r, d, fs in os.walk('skills'):
    for f in fs:
        path = os.path.join(r, f)
        if 'user-skills' in path or 'SKILL.md' in f:
            print("  File:", path, "size:", os.path.getsize(path))

print("\n=== REMOTE DB PERSONAL_CHATS ===")
if os.path.exists('aarkaai.db'):
    conn = sqlite3.connect('aarkaai.db')
    c = conn.cursor()
    c.execute("SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 20")
    for row in c.fetchall():
        print(f"ID: {row[0]} | Session: {row[1]} | Role: {row[2]} | Message: {row[3][:300]}...")
    conn.close()
else:
    print("aarkaai.db not found in CWD")
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
