"""
AARKAAI – SSH/SCP Direct Deployer
Deploys all updated/new files directly to /home/ubuntu/aarkaai3b via SSH/SCP
using C:\\Users\\daarv\\Downloads\\aarkaai7b.pem
"""
import os
import subprocess

KEY_PATH = r"C:\Users\daarv\Downloads\aarkaai7b.pem"
REMOTE_HOST = "ubuntu@16.170.206.243"
REMOTE_DIR = "/home/ubuntu/aarkaai3b"

# Root-level files to deploy
root_files = [
    "config.py",
    "schemas.py",
    "database.py",
    "main.py",
    "pipeline.py",
    "middleware.py",
    "requirements.txt",
    "migrate_add_role.py",
    "admin_db_setup.py",
    "nginx_site.conf",
    "nginx_timeout.conf",
    "FinGenIQ_route.ts",
    ".env.production.template",
]

# Full directories to deploy (rsync -r)
directories_to_deploy = [
    "modules/",
    "skills/",
]

def main():
    print("=" * 60)
    print("AARKAAI SECURE DIRECT SSH DEPLOYMENT")
    print("=" * 60)

    ssh_opts = ["-o", "StrictHostKeyChecking=no", "-i", KEY_PATH]

    # 1. Deploy root-level files via SCP
    print(f"\n[1/4] Uploading {len(root_files)} root files...")
    for filepath in root_files:
        if os.path.exists(filepath):
            scp_cmd = ["scp"] + ssh_opts + [
                filepath,
                f"{REMOTE_HOST}:{REMOTE_DIR}/{filepath}"
            ]
            r = subprocess.run(scp_cmd, capture_output=True, text=True)
            status = "OK" if r.returncode == 0 else f"FAIL: {r.stderr.strip()}"
            print(f"  {filepath} -> {status}")
        else:
            print(f"  WARNING: {filepath} missing locally")

    # 2. Deploy full directories via SCP -r
    print(f"\n[2/4] Uploading {len(directories_to_deploy)} directories...")
    for dirpath in directories_to_deploy:
        if os.path.isdir(dirpath):
            scp_cmd = ["scp", "-r"] + ssh_opts + [
                dirpath.rstrip("/"),
                f"{REMOTE_HOST}:{REMOTE_DIR}/"
            ]
            r = subprocess.run(scp_cmd, capture_output=True, text=True)
            status = "OK" if r.returncode == 0 else f"FAIL: {r.stderr.strip()}"
            print(f"  {dirpath} -> {status}")
        else:
            print(f"  WARNING: {dirpath} directory missing locally")

    def safe_print(text):
        if not text:
            return ""
        return text.encode("ascii", "replace").decode("ascii")

    # 3. Run Remote Migrations & Nginx Configuration
    print("\n[3/4] Running migrations and configuring Nginx on remote server...")
    remote_setup_cmd = (
        f"cd {REMOTE_DIR} && "
        f"if [ ! -f .env ]; then cp .env.production.template .env; fi && "
        f"{REMOTE_DIR}/venv/bin/python migrate_add_role.py && "
        f"{REMOTE_DIR}/venv/bin/python admin_db_setup.py && "
        f"sudo cp nginx_site.conf /etc/nginx/sites-enabled/aarkaai && "
        f"sudo nginx -t && "
        f"sudo systemctl reload nginx && "
        f"echo 'MIGRATION_AND_NGINX_SUCCESS'"
    )
    ssh_cmd = ["ssh"] + ssh_opts + [REMOTE_HOST, remote_setup_cmd]
    r = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    print(f"  Migration & Nginx Output: {safe_print(r.stdout).strip()}")
    if r.stderr:
        print(f"  Migration & Nginx Stderr: {safe_print(r.stderr).strip()}")

    # 4. Restart backend via PM2 (persistent process manager)
    print("\n[4/4] Restarting backend via PM2...")
    remote_script = (
        f"cd {REMOTE_DIR} && "
        f"pm2 restart aarkaai-backend || pm2 start '{REMOTE_DIR}/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 --env-file .env' --name aarkaai-backend && "
        f"pm2 save && "
        f"echo 'PM2_RESTART_SUCCESS'"
    )

    ssh_cmd = ["ssh"] + ssh_opts + [REMOTE_HOST, remote_script]
    r = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="ignore")
    print(f"  PM2 Backend Restart: {safe_print(r.stdout).strip()}")
    if r.stderr:
        print(f"  PM2 Backend Stderr: {safe_print(r.stderr).strip()}")

    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETED AND PERSISTED VIA PM2!")
    print("=" * 60)

if __name__ == "__main__":
    main()
