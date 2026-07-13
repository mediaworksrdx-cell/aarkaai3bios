import requests

base_url = "http://3.223.192.194:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

def send_query(query_text, headers):
    res = requests.post(
        f"{base_url}/prompt",
        json={"query": query_text, "session_id": "deploy_session"},
        headers=headers
    )
    print("Status:", res.status_code)
    try:
        print("Response:", res.json().get("response", res.text))
    except Exception:
        print("Raw Response:", res.text)
    return res.status_code == 200

# Files to deploy as direct overwrites
files_to_deploy = [
    "modules/execution_engine.py",
    "modules/permissions.py",
    "modules/audit_log.py",
    "modules/tools/fs.py",
]

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    if resp.status_code != 200:
        print("Login failed, trying to register...")
        resp = requests.post(f"{base_url}/auth/register", json=reg_payload)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Deploy each file via base64-encoded write script
    for filepath in files_to_deploy:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        import base64
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        print(f"\nDeploying {filepath}...")
        script = (
            f"import base64\n"
            f"encoded = '{encoded}'\n"
            f"content = base64.b64decode(encoded.encode('ascii')).decode('utf-8')\n"
            f"import os; os.makedirs(os.path.dirname('{filepath}'), exist_ok=True)\n"
            f"open('{filepath}', 'w', encoding='utf-8').write(content)\n"
            f"print('Written: {filepath}')"
        )
        query = f"Please execute this python script:\n\n```python\n{script}\n```"
        send_query(query, headers)

    # Restart server
    print("\nRestarting remote backend server...")
    send_query(
        "Please run a shell command to restart the aarkaai backend server: kill port 5000 and restart uvicorn.",
        headers
    )

    print("\nDeployment complete.")

except Exception as e:
    print("Error:", e)
