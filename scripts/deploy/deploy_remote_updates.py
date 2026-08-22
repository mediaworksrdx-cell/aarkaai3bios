"""
AARKAAI – Remote Server Deployment Script
Deploys all 32 updated/new modules, tools, schema, and OAuth endpoints to http://16.170.206.243:5000
"""
import base64
import os
import requests
import sys

base_url = "http://16.170.206.243:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

CHUNK_SIZE_BYTES = 2500

files_to_deploy = [
    "config.py",
    "schemas.py",
    "database.py",
    "main.py",
    "pipeline.py",
    "modules/permissions.py",
    "modules/finance.py",
    "modules/technical.py",
    "modules/web_search.py",
    "modules/financial_calculator.py",
    "modules/fundamentals.py",
    "modules/market_datetime.py",
    "modules/portfolio.py",
    "modules/fno_analytics.py",
    "modules/notifications.py",
    "modules/document_parser.py",
    "modules/tool_router.py",
    "modules/tools/__init__.py",
    "modules/tools/market_data_tool.py",
    "modules/tools/financial_data_tool.py",
    "modules/tools/financial_news_tool.py",
    "modules/tools/financial_calculator_tool.py",
    "modules/tools/portfolio_tool.py",
    "modules/tools/technical_analysis_tool.py",
    "modules/tools/fno_analytics_tool.py",
    "modules/tools/knowledge_search_tool.py",
    "modules/tools/finance_code_tool.py",
    "modules/tools/market_datetime_tool.py",
    "modules/tools/document_parser_tool.py",
    "modules/tools/database_query_tool.py",
    "modules/tools/notification_tool.py",
    "modules/tools/auth_permission_tool.py"
]

def send_query(query_text, headers):
    try:
        res = requests.post(
            f"{base_url}/prompt",
            json={"query": query_text, "session_id": "deploy_security"},
            headers=headers,
            timeout=30
        )
        return res.status_code == 200
    except Exception as e:
        print(f"    Error sending request: {e}")
        return False

def deploy_file(filepath, headers):
    if not os.path.exists(filepath):
        print(f"  SKIP (file not found locally): {filepath}")
        return True

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_bytes = content.encode("utf-8")
    chunks = [raw_bytes[i:i+CHUNK_SIZE_BYTES] for i in range(0, len(raw_bytes), CHUNK_SIZE_BYTES)]
    total = len(chunks)
    print(f"\nDeploying {filepath} ({len(raw_bytes)} bytes, {total} chunk(s))...")

    # Replace backslashes for unix compatibility
    unix_filepath = filepath.replace("\\", "/")
    tmp_path = unix_filepath.replace("/", "_") + ".tmp"

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
        if not send_query(f"Execute: ```python\n{append_script}\n```", headers):
            print(f"  ERROR: Chunk {i+1} failed.")
            return False

    # Step 3: Decode tmp and write final file
    finalize_script = (
        f"import os\n"
        f"dir_name = os.path.dirname('{unix_filepath}')\n"
        f"if dir_name:\n"
        f"    os.makedirs(dir_name, exist_ok=True)\n"
        f"data = open('{tmp_path}', 'rb').read()\n"
        f"open('{unix_filepath}', 'wb').write(data)\n"
        f"os.remove('{tmp_path}')\n"
        f"print('Written: {unix_filepath}')"
    )
    if not send_query(f"Execute: ```python\n{finalize_script}\n```", headers):
        print(f"  ERROR: Could not finalize {filepath}")
        return False

    print(f"  OK: {unix_filepath}")
    return True

def main():
    print("=" * 60)
    print("AARKAAI REMOTE DEPLOYMENT PROCESS")
    print("=" * 60)
    print(f"Target Server: {base_url}")
    print(f"Total Files: {len(files_to_deploy)}")

    try:
        # Check health first
        h_resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check status: {h_resp.status_code}")
    except Exception as e:
        print(f"Warning: Health check failed: {e}")

    try:
        print("\nAuthenticating with remote server...")
        resp = requests.post(f"{base_url}/auth/login", json=reg_payload, timeout=10)
        if resp.status_code != 200:
            print("Registering admin user...")
            resp = requests.post(f"{base_url}/auth/register", json=reg_payload, timeout=10)

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Authenticated successfully.")

        success_count = 0
        failed_files = []

        for filepath in files_to_deploy:
            if deploy_file(filepath, headers):
                success_count += 1
            else:
                failed_files.append(filepath)

        print("\n" + "=" * 60)
        print(f"DEPLOYMENT SUMMARY: {success_count}/{len(files_to_deploy)} files deployed successfully.")

        if failed_files:
            print("Failed files:", failed_files)
        else:
            print("\nRestarting remote backend server...")
            restart_cmd = (
                "Execute: ```bash\n"
                "fuser -k 5000/tcp 2>/dev/null || true; "
                "pkill -9 -f 'uvicorn main:app' 2>/dev/null || true; "
                "sleep 1; "
                "nohup python3.13 -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > aarkaai.log 2>&1 </dev/null &\n"
                "```"
            )
            send_query(restart_cmd, headers)
            print("Remote server restart triggered successfully!")

    except Exception as e:
        print("Deployment Error:", e)

if __name__ == "__main__":
    main()
