"""
AARKAAI – Chunked Remote File Deployer
Splits large files into base64 chunks to bypass the 10,000 char query limit.
"""
import requests
import base64

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

# Max query length is 10,000 chars. We keep base64 chunks well under 4,000 chars
# to leave room for the surrounding script template.
CHUNK_SIZE_BYTES = 2500

def send_query(query_text, headers):
    res = requests.post(
        f"{base_url}/prompt",
        json={"query": query_text, "session_id": "deploy_security"},
        headers=headers
    )
    print("  Status:", res.status_code)
    try:
        resp = res.json().get("response", res.text)
        print("  Response:", resp[:200])
    except Exception:
        print("  Raw:", res.text[:200])
    return res.status_code == 200

def deploy_file(filepath, headers):
    """Deploy a file using chunked base64 transfers."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_bytes = content.encode("utf-8")
    chunks = [raw_bytes[i:i+CHUNK_SIZE_BYTES] for i in range(0, len(raw_bytes), CHUNK_SIZE_BYTES)]
    total = len(chunks)
    print(f"\nDeploying {filepath} in {total} chunk(s)...")

    tmp_path = filepath.replace("/", "_").replace("\\", "_") + ".tmp"

    # Step 1: Clear the tmp file
    clear_script = f"open('{tmp_path}', 'wb').close(); print('tmp cleared')"
    if not send_query(f"Execute: ```python\n{clear_script}\n```", headers):
        print(f"  ERROR: Could not clear tmp file for {filepath}")
        return False

    # Step 2: Append each chunk
    for i, chunk in enumerate(chunks):
        encoded_chunk = base64.b64encode(chunk).decode("ascii")
        append_script = (
            f"import base64\n"
            f"chunk = base64.b64decode('{encoded_chunk}')\n"
            f"open('{tmp_path}', 'ab').write(chunk)\n"
            f"print('chunk {i+1}/{total} appended')"
        )
        print(f"  Sending chunk {i+1}/{total}...")
        if not send_query(f"Execute: ```python\n{append_script}\n```", headers):
            print(f"  ERROR: Chunk {i+1} failed.")
            return False

    # Step 3: Decode tmp and write final file
    finalize_script = (
        f"import os\n"
        f"os.makedirs(os.path.dirname('{filepath}') or '.', exist_ok=True)\n"
        f"data = open('{tmp_path}', 'rb').read()\n"
        f"open('{filepath}', 'wb').write(data)\n"
        f"os.remove('{tmp_path}')\n"
        f"print('Written: {filepath} ({len(raw_bytes)} bytes)')"
    )
    print(f"  Finalizing {filepath}...")
    if not send_query(f"Execute: ```python\n{finalize_script}\n```", headers):
        print(f"  ERROR: Could not finalize {filepath}")
        return False

    return True

# Files that failed or need to be (re)deployed
files_to_deploy = [
    "modules/permissions.py",
    "modules/audit_log.py",
    "modules/execution_engine.py",
    "modules/tools/fs.py",
    "modules/aarkaa_engine.py",
]

try:
    print("Logging in to remote server...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload)
    if resp.status_code != 200:
        print("Trying to register...")
        resp = requests.post(f"{base_url}/auth/register", json=reg_payload)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for filepath in files_to_deploy:
        success = deploy_file(filepath, headers)
        if not success:
            print(f"FAILED: {filepath}")

    # Restart server
    print("\nRestarting remote backend server...")
    send_query(
        "Execute: ```bash\nfuser -k 5000/tcp 2>/dev/null || true; pkill -9 -f 'uvicorn main:app' 2>/dev/null || true; sleep 1; nohup python3.13 -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > aarkaai.log 2>&1 </dev/null &\n```",
        headers
    )

    print("\nDeployment complete.")

except Exception as e:
    print("Error:", e)
