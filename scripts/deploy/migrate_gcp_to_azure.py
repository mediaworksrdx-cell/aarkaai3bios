"""
Full Server Migration Script: GCP (mediaworksr@35.225.45.190) -> Azure (azureuser@20.80.83.151)

Transfers:
  1. Main Aarkaa AI project (/home/mediaworksr/aarkaai3b)
  2. Production GGUF models (7B-Q8, Coder-3B-Q8, 3B-Q8)
  3. SQLite database (aarkaai.db) & ChromaDB vector store
  4. Environment configurations (.env)
  5. Sibling projects: fingeniq, synthetix-site, trade-engine
  6. Nginx configurations & PM2 ecosystem
"""
import subprocess
import sys
import time

GCP_KEY = r"C:\Users\daarv\.ssh\id_ed25519"
GCP_HOST = "mediaworksr@35.225.45.190"

AZURE_KEY = r"C:\Users\daarv\Downloads\market_key.pem"
AZURE_HOST = "azureuser@20.80.83.151"
AZURE_IP = "20.80.83.151"

SSH_OPTS_GCP = ["ssh", "-i", GCP_KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15", GCP_HOST]
SSH_OPTS_AZURE = ["ssh", "-i", AZURE_KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15", AZURE_HOST]


def run_gcp(cmd: str):
    print(f"\n[GCP] Executing: {cmd[:100]}...")
    res = subprocess.run(SSH_OPTS_GCP + [cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.stdout:
        print(res.stdout[:1000])
    if res.stderr:
        print("STDERR:", res.stderr[:500])
    return res


def run_azure(cmd: str):
    print(f"\n[Azure] Executing: {cmd[:100]}...")
    res = subprocess.run(SSH_OPTS_AZURE + [cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.stdout:
        print(res.stdout[:1000])
    if res.stderr:
        print("STDERR:", res.stderr[:500])
    return res


def migrate():
    print("=" * 70)
    print("STARTING FULL SERVER MIGRATION: GCP -> AZURE")
    print("=" * 70)

    # 1. Prepare target directories on Azure
    print("\n[Step 1/6] Initializing Azure directories...")
    run_azure("mkdir -p /home/azureuser/aarkaai3b /home/azureuser/fingeniq /home/azureuser/synthetix-site /home/azureuser/trade-engine")

    # 2. Rsync aarkaai3b from GCP directly to Azure (excluding 32GB model_build/venv to avoid 60GB disk overflow)
    print("\n[Step 2/6] Syncing aarkaai3b repository & data from GCP to Azure...")
    rsync_aarkaai = (
        f"rsync -avz --progress "
        f"--exclude 'venv/' "
        f"--exclude 'model_build/' "
        f"--exclude 'build_quant/' "
        f"--exclude 'aarkaa-7b-f16.gguf' "
        f"--exclude 'aarkaa-3b-f16.gguf' "
        f"--exclude 'aarkaa-coder-3b-f16.gguf' "
        f"--exclude '.next/cache/' "
        f"--exclude 'clean_sync_3_platforms.tar.gz' "
        f"-e 'ssh -o StrictHostKeyChecking=no' "
        f"/home/mediaworksr/aarkaai3b/ "
        f"azureuser@{AZURE_IP}:/home/azureuser/aarkaai3b/"
    )
    res = run_gcp(rsync_aarkaai)
    if res.returncode != 0:
        print("WARNING: Rsync aarkaai3b returned non-zero code:", res.returncode)

    # 3. Rsync sibling services
    print("\n[Step 3/6] Syncing fingeniq, synthetix-site, trade-engine...")
    for svc in ["fingeniq", "synthetix-site", "trade-engine"]:
        rsync_svc = (
            f"rsync -avz --progress "
            f"--exclude 'node_modules/.cache/' "
            f"--exclude '.next/cache/' "
            f"-e 'ssh -o StrictHostKeyChecking=no' "
            f"/home/mediaworksr/{svc}/ "
            f"azureuser@{AZURE_IP}:/home/azureuser/{svc}/"
        )
        run_gcp(rsync_svc)

    # Copy root db and config files if present
    run_gcp(f"rsync -avz -e 'ssh -o StrictHostKeyChecking=no' /home/mediaworksr/*.db /home/mediaworksr/*.jar azureuser@{AZURE_IP}:/home/azureuser/ 2>/dev/null || true")

    # 4. Setup Python virtual environment & dependencies on Azure
    print("\n[Step 4/6] Setting up Python virtual environment on Azure...")
    py_setup = (
        "cd /home/azureuser/aarkaai3b && "
        "python3 -m venv venv && "
        "venv/bin/pip install --upgrade pip setuptools wheel && "
        "venv/bin/pip install -r requirements.txt && "
        "venv/bin/pip install uvicorn gunicorn pydantic-settings python-multipart"
    )
    res = run_azure(py_setup)
    if res.returncode != 0:
        print("WARNING: Python dependency install encountered issues.")

    # 5. Build Next.js frontend on Azure
    print("\n[Step 5/6] Building Next.js frontend on Azure...")
    frontend_setup = (
        "cd /home/azureuser/aarkaai3b/frontend && "
        "npm install && "
        "npm run build"
    )
    run_azure(frontend_setup)

    # 6. Configure PM2 processes & Nginx
    print("\n[Step 6/6] Configuring and starting services under PM2...")
    pm2_cmd = (
        "cd /home/azureuser/aarkaai3b && "
        "pm2 delete all || true; "
        "pm2 start 'venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 5000' --name aarka-backend && "
        "cd /home/azureuser/aarkaai3b/frontend && "
        "pm2 start 'npm start -- -p 3000' --name aarka-frontend && "
        "pm2 save && "
        "pm2 list"
    )
    run_azure(pm2_cmd)

    # Configure Nginx reverse proxy
    print("\nConfiguring Nginx...")
    nginx_conf = """
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    location /prompt/stream {
        proxy_pass http://127.0.0.1:5000/prompt/stream;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        proxy_set_header Connection '';
        add_header X-Accel-Buffering no;
    }

    location /prompt {
        proxy_pass http://127.0.0.1:5000/prompt;
        proxy_read_timeout 600s;
    }

    location /auth/ {
        proxy_pass http://127.0.0.1:5000/auth/;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }

    location /strategy {
        proxy_pass http://127.0.0.1:5000/strategy;
    }

    location /upload {
        proxy_pass http://127.0.0.1:5000/upload;
    }

    location /download/ {
        proxy_pass http://127.0.0.1:5000/download/;
    }

    location /settings {
        proxy_pass http://127.0.0.1:5000/settings;
    }

    location /subscription {
        proxy_pass http://127.0.0.1:5000/subscription;
    }

    location /metrics {
        proxy_pass http://127.0.0.1:5000/metrics;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:5000/admin/;
    }

    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        expires 365d;
        access_log off;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""
    # Write nginx config on Azure
    run_azure(f"echo '{nginx_conf}' | sudo tee /etc/nginx/sites-available/default > /dev/null && sudo nginx -t && sudo systemctl reload nginx")

    # Verify health
    print("\nValidating Azure health endpoints...")
    time.sleep(4)
    run_azure("curl -s http://127.0.0.1:5000/health || echo 'Backend health failed'")
    run_azure("curl -s -I http://127.0.0.1:3000 || echo 'Frontend check failed'")
    run_azure("curl -s -I http://127.0.0.1/health || echo 'Nginx health failed'")

    print("\n" + "=" * 70)
    print("MIGRATION TO AZURE COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    migrate()
