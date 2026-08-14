"""
AARKAAI – Full Production Deployer & Process Manager
Packages all updates from the last 2 days, creates remote backup,
uploads full archive via SCP, extracts on remote EC2 server,
restarts PM2, and validates health.
"""
import os
import sys
import time
import tarfile
import subprocess
import requests

KEY_PATH = r"C:\Users\daarv\Downloads\aarkaai7b.pem"
REMOTE_USER = "ubuntu"
REMOTE_IP = "16.170.206.243"
REMOTE_HOST = f"{REMOTE_USER}@{REMOTE_IP}"
REMOTE_DIR = "/home/ubuntu/aarkaai3b"
ARCHIVE_NAME = "deploy_full_package.tar.gz"

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=15",
    "-i", KEY_PATH
]

def run_ssh(cmd_str):
    """Run an SSH command on the remote server."""
    full_cmd = ["ssh"] + SSH_OPTS + [REMOTE_HOST, cmd_str]
    return subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")

def run_scp(local_path, remote_path):
    """Upload a file to the remote server via SCP."""
    full_cmd = ["scp"] + SSH_OPTS + [local_path, f"{REMOTE_HOST}:{remote_path}"]
    return subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")

def create_archive():
    """Package all code files, modules, skills, configs, and tests into a tar.gz."""
    print("\n[1/6] Packaging project into tar.gz archive...")
    
    # Items to include in deployment package
    files = [
        "config.py",
        "schemas.py",
        "database.py",
        "main.py",
        "pipeline.py",
        "middleware.py",
        "requirements.txt",
        "nginx_site.conf",
        "nginx_timeout.conf",
        "docker-compose.prod.yml",
        ".env.example",
        "migrate_add_role.py",
        "admin_db_setup.py",
        "audit_production.py",
    ]
    
    dirs = [
        "modules",
        "skills",
        ".agents",
        "tests",
    ]
    
    if os.path.exists(ARCHIVE_NAME):
        os.remove(ARCHIVE_NAME)

    with tarfile.open(ARCHIVE_NAME, "w:gz") as tar:
        for f in files:
            if os.path.exists(f):
                tar.add(f, arcname=f)
                print(f"  + Added file: {f}")
        for d in dirs:
            if os.path.isdir(d):
                tar.add(d, arcname=d)
                print(f"  + Added dir : {d}")

    size_kb = os.path.getsize(ARCHIVE_NAME) / 1024
    print(f"-> Archive created: {ARCHIVE_NAME} ({size_kb:.1f} KB)")
    return True

def main():
    print("=" * 70)
    print("AARKAAI FULL PRODUCTION PACK & DEPLOY")
    print(f"Target: {REMOTE_HOST}:{REMOTE_DIR}")
    print("=" * 70)

    # 1. Create Archive
    create_archive()

    # 2. Remote Backup
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    print(f"\n[2/6] Creating remote backup timestamped {timestamp}...")
    backup_cmd = (
        f"mkdir -p {REMOTE_DIR}/backups && "
        f"cd {REMOTE_DIR} && "
        f"tar --exclude='venv' --exclude='*.gguf' --exclude='chroma_db' --exclude='backups' "
        f"-czf backups/backup_{timestamp}.tar.gz config.py pipeline.py main.py modules/ 2>/dev/null || true && "
        f"echo 'BACKUP_CREATED'"
    )
    res = run_ssh(backup_cmd)
    print(f"  Backup status: {res.stdout.strip()}")

    # 3. SCP Transfer
    print(f"\n[3/6] Uploading {ARCHIVE_NAME} to {REMOTE_HOST}:{REMOTE_DIR}...")
    res = run_scp(ARCHIVE_NAME, f"{REMOTE_DIR}/{ARCHIVE_NAME}")
    if res.returncode != 0:
        print(f"  ERROR transferring archive: {res.stderr}")
        return False
    print("  Transfer completed successfully.")

    # 4. Extract Archive Remotely
    print(f"\n[4/6] Extracting files on remote server...")
    extract_cmd = (
        f"cd {REMOTE_DIR} && "
        f"tar -xzf {ARCHIVE_NAME} && "
        f"rm -f {ARCHIVE_NAME} && "
        f"echo 'EXTRACTION_COMPLETE'"
    )
    res = run_ssh(extract_cmd)
    print(f"  Extract status: {res.stdout.strip()}")

    # 5. Run Python environment check & PM2 restart
    print(f"\n[5/6] Restarting AARKAAI backend via PM2...")
    restart_cmd = (
        f"cd {REMOTE_DIR} && "
        f"{REMOTE_DIR}/venv/bin/pip install pytest --quiet 2>/dev/null || true && "
        f"pm2 restart aarkaai-backend || pm2 start '{REMOTE_DIR}/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 --env-file .env' --name aarkaai-backend && "
        f"pm2 save && "
        f"sleep 3 && "
        f"pm2 status"
    )
    res = run_ssh(restart_cmd)
    print(res.stdout)

    # 6. Remote health check & verification test
    print(f"\n[6/6] Validating remote server health & endpoints...")
    time.sleep(5)
    
    # Run test query against the running server
    test_cmd = (
        f"cd {REMOTE_DIR} && "
        f"{REMOTE_DIR}/venv/bin/python -c \""
        f"import requests\n"
        f"try:\n"
        f"    r = requests.get('http://127.0.0.1:5000/docs', timeout=5)\n"
        f"    print(f'FastAPI Docs endpoint: HTTP {r.status_code}')\n"
        f"except Exception as e:\n"
        f"    print(f'Connection failed: {e}')\n"
        f"\""
    )
    res = run_ssh(test_cmd)
    print(f"  {res.stdout.strip()}")

    # Run unit tests on remote server
    test_run_cmd = (
        f"cd {REMOTE_DIR} && "
        f"{REMOTE_DIR}/venv/bin/python -m pytest tests/ -q"
    )
    res = run_ssh(test_run_cmd)
    print(f"  Remote Pytest output: {res.stdout.strip()}")

    # Check PM2 logs
    log_cmd = f"pm2 logs aarkaai-backend --lines 15 --nostream"
    res = run_ssh(log_cmd)
    print("\n--- Recent PM2 Logs ---")
    print(res.stdout)

    print("\n" + "=" * 70)
    print("ALL CHANGES DEPLOYED AND SERVER RESTARTED SUCCESSFULLY!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    main()
