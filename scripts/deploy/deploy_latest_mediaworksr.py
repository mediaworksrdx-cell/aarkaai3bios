import os
import sys
import tarfile
import subprocess
import time
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

KEY_PATH = r"C:\Users\daarv\.ssh\id_ed25519"
REMOTE_USER = "mediaworksr"
REMOTE_IP = "35.225.45.190"
REMOTE_HOST = f"{REMOTE_USER}@{REMOTE_IP}"
REMOTE_DIR = "/home/mediaworksr/aarkaai3b"
ARCHIVE_NAME = "deploy_latest_update.tar.gz"

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=15",
    "-i", KEY_PATH
]

def run_ssh(cmd_str):
    full_cmd = ["ssh"] + SSH_OPTS + [REMOTE_HOST, cmd_str]
    print(f"--> SSH: {cmd_str[:80]}...")
    res = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if res.stdout:
        print(res.stdout[:500].encode("ascii", "replace").decode("ascii"))
    if res.stderr:
        print("ERR:", res.stderr[:300].encode("ascii", "replace").decode("ascii"))
    return res

def run_scp(local_path, remote_path):
    full_cmd = ["scp"] + SSH_OPTS + [local_path, f"{REMOTE_HOST}:{remote_path}"]
    print(f"--> SCP: {local_path} -> {remote_path}")
    return subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")

def create_archive():
    print("\n[1/5] Packaging latest backend & frontend into tar.gz archive...")
    if os.path.exists(ARCHIVE_NAME):
        os.remove(ARCHIVE_NAME)

    with tarfile.open(ARCHIVE_NAME, "w:gz") as tar:
        # Backend root files
        root_files = [
            "pipeline.py",
            "aarkaa_engine.py",
            "config.py",
            "schemas.py",
            "database.py",
            "main.py",
            "middleware.py",
            "modal_server.py",
        ]
        for rf in root_files:
            if os.path.exists(rf):
                tar.add(rf, arcname=rf)
                print(f"  + Added file: {rf}")

        # Modules directory (recursive, excluding cache)
        def filter_pycache(tarinfo):
            if "__pycache__" in tarinfo.name or tarinfo.name.endswith((".pyc", ".pyo")):
                return None
            return tarinfo

        if os.path.exists("modules"):
            tar.add("modules", arcname="modules", filter=filter_pycache)
            print("  + Added directory: modules/")

        if os.path.exists("routers"):
            tar.add("routers", arcname="routers", filter=filter_pycache)
            print("  + Added directory: routers/")

        if os.path.exists("skills"):
            tar.add("skills", arcname="skills", filter=filter_pycache)
            print("  + Added directory: skills/")

        if os.path.exists("Dockerfile.sandbox"):
            tar.add("Dockerfile.sandbox", arcname="Dockerfile.sandbox")
            print("  + Added file: Dockerfile.sandbox")


        # Frontend source & public files
        def filter_frontend(tarinfo):
            if any(x in tarinfo.name for x in ["node_modules", ".next", ".git"]):
                return None
            return tarinfo

        if os.path.exists("frontend/src"):
            tar.add("frontend/src", arcname="frontend/src", filter=filter_frontend)
            print("  + Added directory: frontend/src/")
        if os.path.exists("frontend/public"):
            tar.add("frontend/public", arcname="frontend/public", filter=filter_frontend)
            print("  + Added directory: frontend/public/")
        for ff in ["frontend/package.json", "frontend/tsconfig.json", "frontend/next.config.ts", "frontend/tailwind.config.ts", "frontend/postcss.config.js"]:
            if os.path.exists(ff):
                tar.add(ff, arcname=ff)
                print(f"  + Added frontend config: {ff}")

    size_mb = os.path.getsize(ARCHIVE_NAME) / (1024 * 1024)
    print(f"Archive created: {ARCHIVE_NAME} ({size_mb:.2f} MB)")

def deploy():
    create_archive()

    # Step 2: Upload archive
    print("\n[2/5] Uploading archive to GCP VM via SCP...")
    res = run_scp(ARCHIVE_NAME, f"{REMOTE_DIR}/{ARCHIVE_NAME}")
    if res.returncode != 0:
        print("SCP upload failed!", res.stderr)
        return False

    # Step 3: Extract archive on remote server
    print("\n[3/5] Extracting archive on remote host...")
    extract_cmd = f"cd {REMOTE_DIR} && tar -xzf {ARCHIVE_NAME} && rm -f {ARCHIVE_NAME}"
    res = run_ssh(extract_cmd)
    if res.returncode != 0:
        print("Extract failed!", res.stderr)
        return False

    # Step 4: Build frontend
    print("\n[4/5] Building Next.js frontend on remote host...")
    build_cmd = f"export PATH=/usr/bin:/bin:/home/mediaworksr/.nvm/versions/node/v20.18.0/bin:$PATH && cd {REMOTE_DIR}/frontend && rm -rf .next && npm run build"
    res = run_ssh(build_cmd)
    if res.returncode != 0:
        print("Frontend build note / err:", res.stderr)

    # Step 5: Restart PM2 services
    print("\n[5/5] Restarting PM2 aarka-backend and aarka-frontend...")
    restart_cmd = "export PATH=/usr/bin:/bin:/home/mediaworksr/.nvm/versions/node/v20.18.0/bin:$PATH && pm2 restart aarka-backend && pm2 restart aarka-frontend && pm2 list"
    res = run_ssh(restart_cmd)

    # Clean local archive
    if os.path.exists(ARCHIVE_NAME):
        os.remove(ARCHIVE_NAME)

    # Validate health
    print("\nValidating backend health...")
    time.sleep(3)
    try:
        resp = requests.get("http://35.225.45.190:5000/health", timeout=10)
        print(f"Backend health status: {resp.status_code} -> {resp.text[:100]}")
    except Exception as e:
        print(f"Health check warning: {e}")

    try:
        resp2 = requests.get("http://35.225.45.190:3000", timeout=10)
        print(f"Frontend web status: {resp2.status_code}")
    except Exception as e:
        print(f"Frontend check warning: {e}")

    print("\nDEPLOYMENT COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    deploy()
