import os
import shutil
import zipfile
import subprocess
import time

# ─── Configuration ────────────────────────────────────────────────────────────
PEM_KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
PORT = 22
USER = "ec2-user"
REMOTE_DIR = "/workspace/synthetix-site"
ZIP_NAME = "site_update.zip"

SITE_SRC_DIR = r"c:\Users\daarv\.gemini\antigravity\scratch\synthetix-site"
STANDALONE_DIR = os.path.join(SITE_SRC_DIR, ".next", "standalone")
STATIC_DIR = os.path.join(SITE_SRC_DIR, ".next", "static")
PUBLIC_DIR = os.path.join(SITE_SRC_DIR, "public")

# ─── Step 1: Copy assets to standalone directory ─────────────────────────────
print("Step 1: Copying public and static assets to standalone folder...")
if not os.path.exists(STANDALONE_DIR):
    print("Error: .next/standalone does not exist. Please run next build first.")
    exit(1)

# Copy public
dest_public = os.path.join(STANDALONE_DIR, "public")
if os.path.exists(dest_public):
    shutil.rmtree(dest_public)
if os.path.exists(PUBLIC_DIR):
    shutil.copytree(PUBLIC_DIR, dest_public)
    print("  Copied public assets.")

# Copy static to standalone/.next/static
dest_static = os.path.join(STANDALONE_DIR, ".next", "static")
if os.path.exists(dest_static):
    shutil.rmtree(dest_static)
if os.path.exists(STATIC_DIR):
    shutil.copytree(STATIC_DIR, dest_static)
    print("  Copied static CSS/JS assets.")

# ─── Step 2: Package standalone folder into ZIP ──────────────────────────────
print("\nStep 2: Packaging standalone files...")
local_zip_path = os.path.join(SITE_SRC_DIR, ZIP_NAME)
with zipfile.ZipFile(local_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(STANDALONE_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, STANDALONE_DIR)
            zipf.write(file_path, arcname)
print(f"Packaging complete. Created {local_zip_path}")

# ─── Step 3: Upload ZIP to remote server ─────────────────────────────────────
print("\nStep 3: Uploading ZIP to remote server...")
scp_cmd = [
    "scp",
    "-P", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    local_zip_path,
    f"{USER}@{HOST}:/home/ec2-user/"
]
print("Running SCP command...")
result = subprocess.run(scp_cmd, capture_output=True, text=True, encoding="utf-8")
if result.returncode != 0:
    print(f"SCP failed: {result.stderr}")
    exit(1)
print("Upload successful.")

# Remove local ZIP
if os.path.exists(local_zip_path):
    os.remove(local_zip_path)

# ─── Step 4: Run Remote SSH commands to deploy ───────────────────────────────
print("\nStep 4: Executing remote deployment commands via SSH...")

remote_commands = f"""
set -e
sudo mkdir -p {REMOTE_DIR}
sudo chown -R ec2-user:ec2-user {REMOTE_DIR}

echo "Extracting new files..."
unzip -o /home/ec2-user/{ZIP_NAME} -d {REMOTE_DIR}
rm -f /home/ec2-user/{ZIP_NAME}

# Create startup script start_site.sh
cat << 'EOF' > {REMOTE_DIR}/start_site.sh
#!/bin/bash
cd {REMOTE_DIR}
echo "Stopping any existing server on port 3000..."
fuser -k 3000/tcp || true
pkill -9 -f "server.js" || true
sleep 1
echo "Starting Next.js server.js on port 3000..."
PORT=3000 AARKAAI_BACKEND_URL=http://127.0.0.1:5000 HOSTNAME=0.0.0.0 nohup node server.js > site.log 2>&1 </dev/null &
echo "Next.js site launched in background."
EOF

chmod +x {REMOTE_DIR}/start_site.sh
{REMOTE_DIR}/start_site.sh
sleep 4
cat {REMOTE_DIR}/site.log
"""

ssh_cmd = [
    "ssh",
    "-p", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    remote_commands
]

print("Running SSH commands...")
result = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8")
print("SSH Command Output:")
print(result.stdout)
if result.returncode != 0:
    print(f"SSH failed: {result.stderr}")
    exit(1)

print("\nDeployment completed successfully!")
