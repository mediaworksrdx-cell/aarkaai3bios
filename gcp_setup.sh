#!/usr/bin/env bash
set -e

echo "========================================================="
echo "   AARKAAI GCP COMPUTE ENGINE VM PROVISIONING & STARTUP   "
echo "========================================================="

APP_DIR="$HOME/aarkaai3b"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

echo "[1/7] Updating system packages and installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git curl wget nginx tar ufw build-essential libpq-dev

echo "[2/7] Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip setuptools wheel

echo "[3/7] Installing Aarkaa AI Python dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found, installing core modules..."
    pip install fastapi uvicorn pydantic python-dotenv pymongo chromadb requests httpx pytest
fi
# Additional required packages for full pipeline & document generator
pip install --quiet chromadb python-docx python-pptx openpyxl pdfplumber pypdf reportlab pyyaml xlsxwriter weasyprint matplotlib || true

echo "[4/7] Configuring Environment Variables..."
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        cp .env.production .env
    elif [ -f .env.example ]; then
        cp .env.example .env
    fi
fi

# Ensure Google Credentials path is exported if the service account json exists
if [ -f "orbital-heaven-504004-s2-df5a0ce91659.json" ]; then
    echo "Configuring GCP Service Account credentials..."
    export GOOGLE_APPLICATION_CREDENTIALS="$APP_DIR/orbital-heaven-504004-s2-df5a0ce91659.json"
fi

echo "[5/7] Configuring Nginx Reverse Proxy..."
if [ -f nginx_gcp.conf ]; then
    sudo cp nginx_gcp.conf /etc/nginx/sites-available/aarkaai
    sudo ln -sf /etc/nginx/sites-available/aarkaai /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx || sudo systemctl restart nginx
fi

echo "[6/7] Setting up Systemd Service (aarkaai)..."
sudo bash -c "cat <<EOF > /etc/systemd/system/aarkaai.service
[Unit]
Description=Aarkaa AI Production Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment=GOOGLE_APPLICATION_CREDENTIALS=$APP_DIR/orbital-heaven-504004-s2-df5a0ce91659.json
ExecStart=$APP_DIR/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable aarkaai
sudo systemctl restart aarkaai

echo "[7/7] Verifying Backend Health..."
sleep 4
sudo systemctl status aarkaai --no-pager

echo ""
echo "Testing local HTTP response..."
curl -s -o /dev/null -w "FastAPI status code: %{http_code}\n" http://127.0.0.1:5000/docs || true

echo "========================================================="
echo "   AARKAAI BACKEND MIGRATED & RUNNING ON GCP SUCCESSFULLY"
echo "========================================================="
