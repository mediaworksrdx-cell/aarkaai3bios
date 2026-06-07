import os
import zipfile
import subprocess
import time
import requests

# ─── Configuration ────────────────────────────────────────────────────────────
PEM_KEY = r"C:\Users\daarv\.ssh\LightsailDefaultKey-ap-south-1 (2).pem"
HOST = "43.204.153.162"
USER = "ubuntu"
REMOTE_DIR = "/home/ubuntu/aarkaai3b"
ZIP_NAME = "aarkaai_update.zip"

FILES_TO_PACK = [
    "config.py",
    "database.py",
    "main.py",
    "pipeline.py",
    "register_visitor.py",
    "schemas.py",
    "modules/aarkaa_engine.py",
    "modules/auto_learn.py",
    "modules/finance.py",
    "modules/memory.py",
    "modules/options_strategy.py",
    "modules/subscription.py",
    "modules/technical.py",
    "modules/web_search.py",
    "modules/semantic_filter.py",
    "modules/rag.py",
    "scratch/remote_db_migrate.py",
]

# ─── Step 1: Package Files into ZIP ──────────────────────────────────────────
print("Step 1: Packaging updated files...")
with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
    for file_path in FILES_TO_PACK:
        if os.path.exists(file_path):
            zipf.write(file_path)
            print(f"  Added {file_path}")
        else:
            print(f"  Warning: File {file_path} not found!")

print("Packaging complete.")

# ─── Step 2: Upload via SCP ──────────────────────────────────────────────────
print("\nStep 2: Uploading ZIP to remote server...")
scp_cmd = [
    "scp",
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    ZIP_NAME,
    f"{USER}@{HOST}:{REMOTE_DIR}/"
]

print("Running command:", " ".join(scp_cmd))
result = subprocess.run(scp_cmd, capture_output=True, text=True, encoding="utf-8")
if result.returncode != 0:
    print(f"SCP failed: {result.stderr}")
    exit(1)
print("Upload successful.")

# Remove local zip
if os.path.exists(ZIP_NAME):
    os.remove(ZIP_NAME)

# ─── Step 3: Run Remote SSH Deployment Commands ─────────────────────────────
print("\nStep 3: Executing remote deployment commands via SSH...")

remote_commands = f"""
set -e
cd {REMOTE_DIR}

# 1. Create a backup of existing files
echo "Creating backup of current files..."
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz config.py database.py main.py pipeline.py register_visitor.py schemas.py modules/aarkaa_engine.py modules/auto_learn.py modules/finance.py modules/memory.py modules/options_strategy.py modules/subscription.py modules/technical.py modules/web_search.py modules/semantic_filter.py

# 2. Extract update zip
echo "Extracting updated files..."
unzip -o {ZIP_NAME}
rm {ZIP_NAME}

# 3. Run database migrations (only if migration script was sent)
echo "Checking for database migrations..."
if [ -f scratch/remote_db_migrate.py ]; then
    echo "Running database migrations..."
    if [ -f venv/bin/python ]; then
        venv/bin/python scratch/remote_db_migrate.py
    else
        python3 scratch/remote_db_migrate.py
    fi
    rm -f scratch/remote_db_migrate.py
else
    echo "No migration script, skipping migration."
fi

# 4. Restart backend service
echo "Restarting aarkaai systemd service..."
sudo systemctl restart aarkaai.service

echo "Checking service status..."
sudo systemctl status aarkaai.service --no-pager -l
"""

ssh_cmd = [
    "ssh",
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    f"{USER}@{HOST}",
    remote_commands
]

print("Running SSH commands...")
result = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8")
print("SSH Command Output:")
print(result.stdout.encode('ascii', 'ignore').decode('ascii'))
if result.returncode != 0:
    print(f"SSH failed: {result.stderr.encode('ascii', 'ignore').decode('ascii')}")
    exit(1)

# ─── Step 4: Verify Deployment ───────────────────────────────────────────────
print("\nStep 4: Verifying remote deployment health check...")
health_url = f"http://{HOST}:5000/health"
print(f"Curling {health_url}...")

# Wait a few seconds for LLM to load
time.sleep(5)

for attempt in range(5):
    try:
        res = requests.get(health_url, timeout=10)
        if res.status_code == 200:
            print("Deployment verified successfully! Health check returned 200.")
            print(res.json())
            break
        else:
            print(f"Health check failed with status code: {res.status_code}")
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}")
    time.sleep(3)
else:
    print("Health check could not be verified after 5 attempts.")
