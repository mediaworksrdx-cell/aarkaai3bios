import requests

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
    
    # Send agent task to dump database entries
    task_query = "Please execute a bash command to run python code: import sqlite3; conn=sqlite3.connect('aarkaai.db'); c=conn.cursor(); c.execute('SELECT id, query, response, detected_language FROM conversation_history ORDER BY id DESC LIMIT 10'); [print(r) for r in c.fetchall()]; conn.close()"
    
    print("\nSending prompt request (triggers agent coordinator)...")
    res = requests.post(
        f"{base_url}/prompt", 
        json={"query": task_query, "session_id": "default"}, 
        headers=headers
    )
    print("Status:", res.status_code)
    print("Response JSON:")
    print(res.json())
    
except Exception as e:
    print("Error:", e)
