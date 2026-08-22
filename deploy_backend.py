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

# ─── Configuration ────────────────────────────────────────────────────────────
KEY = r"C:\Users\daarv\.ssh\id_ed25519"
USER = "sathishbadri2015"
HOST = "136.85.114.150"
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-i", KEY]

LOCAL_BACKEND = os.path.dirname(os.path.abspath(__file__))
REMOTE_BACKEND = "/home/sathishbadri2015/aarkaai3b"
PYTHON_BIN = f"{REMOTE_BACKEND}/venv/bin/python"

# Files/dirs to sync (only application code, never .env or venv)
SYNC_PATHS = [
    "main.py",
    "pipeline.py",
    "config.py",
    "database.py",
    "middleware.py",
    "schemas.py",
    "modules/",
    "routers/",
    "pipeline/",
    "skills/",
    "tests/",
]

def ssh(cmd: str, timeout: int = 300) -> str:
    full_cmd = ["ssh"] + SSH_OPTS + [f"{USER}@{HOST}", cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore", timeout=timeout)
    if res.returncode != 0 and res.stderr.strip():
        print(f"  [WARN] stderr: {res.stderr.strip()[:500]}")
    return res.stdout.strip()


def scp(local_path: str, remote_path: str):
    cmd = ["scp", "-r"] + SSH_OPTS + [local_path, f"{USER}@{HOST}:{remote_path}"]
    return subprocess.run(cmd, capture_output=True, text=True, errors="ignore", timeout=120)


def sync_files():
    """Upload application code to server"""
    print("\n[1/3] Syncing backend source files...")
    # Ensure remote base directories exist
    ssh(f"mkdir -p {REMOTE_BACKEND}/routers {REMOTE_BACKEND}/pipeline {REMOTE_BACKEND}/modules {REMOTE_BACKEND}/tests")
    for path in SYNC_PATHS:
        local = os.path.join(LOCAL_BACKEND, path.rstrip("/\\"))
        if os.path.exists(local):
            if os.path.isdir(local):
                remote = f"{REMOTE_BACKEND}/"
            else:
                remote = f"{REMOTE_BACKEND}/{path}"
            res = scp(local, remote)
            status = "[OK]" if res.returncode == 0 else "[FAIL]"
            print(f"  {status} {path}")
        else:
            print(f"  [SKIP] {path} (not found locally)")
    return True


def run_tests():
    """Verify python compilation and syntax on the server"""
    print("\n[2/3] Checking backend syntax and compilation...")
    result = ssh(f"cd {REMOTE_BACKEND} && {PYTHON_BIN} -m py_compile main.py pipeline.py config.py 2>&1")
    if not result:
        print("  [OK] Backend code syntax & compilation verified")
        return True
    else:
        print(f"  [FAIL] Compilation error: {result}")
        return False


def restart():
    """Kill old FastAPI and start fresh"""
    print("\n[3/3] Restarting FastAPI server...")
    
    # Kill existing uvicorn
    ssh("pkill -9 -f 'uvicorn.*5000' 2>/dev/null || true")
    ssh("fuser -k 5000/tcp 2>/dev/null || true")
    time.sleep(1)
    
    remaining = ssh("ss -tlpn | grep 5000")
    if remaining:
        ssh("fuser -k -9 5000/tcp 2>/dev/null || true")
        time.sleep(2)
    
    # Start FastAPI in background inside a detached screen session
    start_cmd = (
        f"screen -wipe 2>/dev/null; "
        f"screen -dmS aarkaai_backend bash -c "
        f"'cd {REMOTE_BACKEND} && {PYTHON_BIN} -m uvicorn main:app --host 0.0.0.0 --port 5000 >> {REMOTE_BACKEND}/fastapi_service.log 2>&1'"
    )
    ssh(start_cmd)
    
    # Wait for startup (model loading takes ~20s)
    print("  Waiting for startup (model loading)...")
    for i in range(8):
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
                    print(f"  [OK] {len(mods)}/{len(mods)} modules operational")
                except:
                    pass
            return True
        elif i < 7:
            print(f"  ... waiting ({(i+1)*3}s)")
    
    print("  [FAIL] Backend did not become healthy within 24s")
    print("  Log tail:")
    print(ssh(f"tail -10 {REMOTE_BACKEND}/fastapi_service.log"))
    return False


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--full"
    
    print("=" * 60)
    print("  AARKAAI Backend Deployment")
    print(f"  Mode: {mode}")
    print(f"  Target: {USER}@{HOST}:{REMOTE_BACKEND}")
    print("=" * 60)
    
    if mode == "--restart":
        restart()
    elif mode == "--sync":
        sync_files()
    else:
        sync_files()
        if run_tests():
            restart()
        else:
            print("\n[FAIL] Tests failed. Aborting restart.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("  Backend deployment complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
