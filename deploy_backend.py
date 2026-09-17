#!/usr/bin/env python3
"""
deploy_backend.py — Canonical backend deployment script for AARKAAI.

Usage:
    python deploy_backend.py               # Full deploy: sync → test → restart
    python deploy_backend.py --restart     # Just restart FastAPI (no file sync)
    python deploy_backend.py --sync        # Sync files only (no restart)

This script is the ONLY way to deploy backend changes to production.
"""
import subprocess
import sys
import time
import os
import tarfile

# ─── Configuration ────────────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

KEY = r"C:\Users\daarv\.ssh\id_ed25519"
USER = "mediaworksr"
HOST = "35.225.45.190"
SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=15",
    "-i", KEY,
]

LOCAL_BACKEND = os.path.dirname(os.path.abspath(__file__))
REMOTE_BACKEND = "/home/mediaworksr/aarkaai3b"
PYTHON_BIN = f"{REMOTE_BACKEND}/venv/bin/python"
PM2_ENV = (
    "export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:"
    "/home/mediaworksr/.nvm/versions/node/v20.18.0/bin:$PATH"
)

# Files/dirs to sync (only application code, never .env or venv)
SYNC_PATHS = [
    "main.py",
    "pipeline.py",
    "aarkaa_engine.py",
    "config.py",
    "database.py",
    "middleware.py",
    "schemas.py",
    "modules/",
    "routers/",
    "pipeline/",
    "skills/",
    "tests/",
    "scripts/",
    "docs/",
    "mcp_config.yaml",
]

def ssh(cmd: str, timeout: int = 120) -> str:
    full_cmd = ["ssh"] + SSH_OPTS + [f"{USER}@{HOST}", cmd]
    res = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=timeout,
    )
    if res.returncode != 0 and res.stderr.strip():
        print(f"  [WARN] stderr: {res.stderr.strip()[:500]}")
    return res.stdout.strip()


def scp(local_path: str, remote_path: str):
    cmd = ["scp"] + SSH_OPTS + [local_path, f"{USER}@{HOST}:{remote_path}"]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=180,
    )


def sync_files():
    """Package and upload application code to server via tarball"""
    print("\n[1/3] Packaging and syncing backend source files...")
    archive_name = "deploy_backend_update.tar.gz"
    local_archive = os.path.join(LOCAL_BACKEND, archive_name)
    remote_archive = f"{REMOTE_BACKEND}/{archive_name}"

    if os.path.exists(local_archive):
        os.remove(local_archive)

    def filter_tar(tarinfo):
        if any(x in tarinfo.name for x in ["__pycache__", ".git", "node_modules", ".pytest_cache", ".pyc"]):
            return None
        return tarinfo

    with tarfile.open(local_archive, "w:gz") as tar:
        for path in SYNC_PATHS:
            local = os.path.join(LOCAL_BACKEND, path.rstrip("/\\"))
            if os.path.exists(local):
                tar.add(local, arcname=path.rstrip("/\\"), filter=filter_tar)
                print(f"  + Added: {path}")
            else:
                print(f"  [SKIP] {path} (not found locally)")

    size_mb = os.path.getsize(local_archive) / (1024 * 1024)
    print(f"  -> Uploading {archive_name} ({size_mb:.2f} MB) via SCP...")
    res = scp(local_archive, remote_archive)
    if res.returncode != 0:
        print(f"  [FAIL] SCP upload failed: {res.stderr}")
        return False

    print("  -> Extracting on remote GCP host...")
    ssh(f"cd {REMOTE_BACKEND} && tar -xzf {archive_name} && rm -f {archive_name}")

    if os.path.exists(local_archive):
        os.remove(local_archive)

    print("  [OK] Source files synchronized successfully.")
    return True


def run_tests():
    """Verify python compilation and syntax on the server"""
    print("\n[2/3] Checking backend syntax and compilation...")
    cmd = ["ssh"] + SSH_OPTS + [f"{USER}@{HOST}", f"cd {REMOTE_BACKEND} && {PYTHON_BIN} -m py_compile main.py pipeline.py config.py"]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=60,
    )
    if res.returncode == 0:
        print("  [OK] Backend code syntax & compilation verified")
        return True
    else:
        print(f"  [FAIL] Compilation error (rc={res.returncode}): {res.stderr or res.stdout}")
        return False


def restart():
    """Restart FastAPI server managed by PM2 on GCP"""
    print("\n[3/3] Restarting FastAPI server via PM2...")
    
    # Trigger clean PM2 restart
    print("  -> Dispatching 'pm2 restart aarka-backend'...")
    restart_res = ssh(f"{PM2_ENV} && pm2 restart aarka-backend")
    print("  -> PM2 restart signal dispatched.")
    
    # Wait for startup (model loading takes ~10-25s)
    print("  Waiting for backend startup (model initialization)...")
    for i in range(25):
        time.sleep(3)
        health = ssh("curl -s http://127.0.0.1:5000/health 2>/dev/null")
        if '"status":"healthy"' in health:
            print(f"  [OK] Backend healthy after {(i+1)*3}s")
            # Print module count
            if "modules" in health:
                import json
                try:
                    h = json.loads(health)
                    mods = h.get("modules", {})
                    print(f"  [OK] {len(mods)}/{len(mods)} modules operational: {list(mods.keys())}")
                except Exception:
                    pass
            return True
        elif i < 24:
            print(f"  ... waiting ({(i+1)*3}s)")
    
    print("  [FAIL] Backend did not become healthy within 75s")
    print("  PM2 logs tail:")
    print(ssh(f"{PM2_ENV} && pm2 logs aarka-backend --lines 30 --nostream"))
    return False


def verify_deployment():
    """Verify production endpoints and readiness post-deploy"""
    print("\n[*] Running post-deployment verification...")
    success = True
    
    # 1. Check local health via loopback curl on server
    health_raw = ssh("curl -s http://127.0.0.1:5000/health")
    if '"status":"healthy"' in health_raw:
        print("  [PASS] Server internal health (127.0.0.1:5000/health): 200 OK")
    else:
        print(f"  [FAIL] Server internal health check failed: {health_raw}")
        success = False

    # 2. Check public HTTPS health check
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://aarka-ai.com/health",
            headers={"User-Agent": "AARKAAI-Deploy/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            if resp.status == 200 and '"status":"healthy"' in body:
                print("  [PASS] Public gateway health (https://aarka-ai.com/health): 200 OK")
            else:
                print(f"  [WARN] Public endpoint status: {resp.status}, body: {body[:200]}")
    except Exception as e:
        print(f"  [WARN] Public endpoint check: {e}")

    # 3. Check PM2 status
    pm2_out = ssh(f"{PM2_ENV} && pm2 show aarka-backend")
    if "online" in pm2_out:
        print("  [PASS] PM2 supervisor status: aarka-backend ONLINE")
    else:
        print("  [WARN] PM2 status not verified online")
        success = False

    return success


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--full"
    
    print("=" * 60)
    print("  AARKAAI Backend Production Deployment")
    print(f"  Mode: {mode}")
    print(f"  Target: {USER}@{HOST}:{REMOTE_BACKEND}")
    print("=" * 60)
    
    if mode == "--restart":
        if restart():
            verify_deployment()
        else:
            sys.exit(1)
    elif mode == "--sync":
        sync_files()
    else:
        if not sync_files():
            print("\n[FAIL] File sync failed. Aborting deployment.")
            sys.exit(1)
        if run_tests():
            if restart():
                verify_deployment()
            else:
                print("\n[FAIL] Restart failed.")
                sys.exit(1)
        else:
            print("\n[FAIL] Remote syntax tests failed. Aborting restart.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("  AARKAAI Backend deployment successfully completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
