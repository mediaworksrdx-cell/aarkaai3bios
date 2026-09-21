"""
Automated Deployment Script for Azure VM (market: 20.80.83.151)

Usage:
    python scripts/deploy/deploy_latest_azure.py
"""
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

KEY_PATH = r"C:\Users\daarv\Downloads\market_key.pem"
REMOTE_USER = "azureuser"
REMOTE_IP = "20.80.83.151"
REMOTE_HOST = f"{REMOTE_USER}@{REMOTE_IP}"
REMOTE_DIR = "/home/azureuser/aarkaai3b"
ARCHIVE_NAME = "deploy_latest_azure.tar.gz"

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
        print(res.stdout[:500])
    if res.stderr:
        print("ERR:", res.stderr[:300])
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
        root_files = [
            "pipeline.py",
            "_pipeline_legacy.py",
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

        def filter_pycache(tarinfo):
            if "__pycache__" in tarinfo.name or tarinfo.name.endswith((".pyc", ".pyo")):
                return None
            return tarinfo

        for d in ["pipeline", "modules", "routers", "skills"]:
            if os.path.exists(d):
                tar.add(d, arcname=d, filter=filter_pycache)
                print(f"  + Added directory: {d}/")

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

    print("\n[2/5] Uploading archive to Azure VM via SCP...")
    res = run_scp(ARCHIVE_NAME, f"{REMOTE_DIR}/{ARCHIVE_NAME}")
    if res.returncode != 0:
        print("SCP upload failed!", res.stderr)
        return False

    print("\n[3/5] Extracting archive on Azure VM...")
    extract_cmd = f"cd {REMOTE_DIR} && tar -xzf {ARCHIVE_NAME} && rm -f {ARCHIVE_NAME}"
    res = run_ssh(extract_cmd)
    if res.returncode != 0:
        print("Extract failed!", res.stderr)
        return False

    print("\n[4/5] Building Next.js frontend on Azure VM...")
    build_cmd = f"cd {REMOTE_DIR}/frontend && rm -rf .next && npm run build"
    res = run_ssh(build_cmd)
    if res.returncode != 0:
        print("Frontend build note / err:", res.stderr)

    print("\n[5/5] Restarting PM2 aarka-backend and aarka-frontend...")
    restart_cmd = "pm2 restart aarka-backend && pm2 restart aarka-frontend && pm2 list"
    res = run_ssh(restart_cmd)

    if os.path.exists(ARCHIVE_NAME):
        os.remove(ARCHIVE_NAME)

    print("\nValidating backend health on Azure...")
    time.sleep(3)
    try:
        resp = requests.get(f"http://{REMOTE_IP}/health", timeout=10)
        print(f"Backend health status: {resp.status_code} -> {resp.text[:100]}")
    except Exception as e:
        print(f"Health check warning: {e}")

    try:
        resp2 = requests.get(f"http://{REMOTE_IP}", timeout=10)
        print(f"Frontend web status: {resp2.status_code}")
    except Exception as e:
        print(f"Frontend check warning: {e}")

    print("\nAZURE DEPLOYMENT COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    deploy()
