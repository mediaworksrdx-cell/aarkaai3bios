#!/usr/bin/env bash
cd "$HOME/aarkaai3b"

echo "Activating virtualenv and loading environment variables..."
source venv/bin/activate

if [ -f "orbital-heaven-504004-s2-df5a0ce91659.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/aarkaai3b/orbital-heaven-504004-s2-df5a0ce91659.json"
fi

# Kill any previous instance
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

echo "Starting AARKAAI Production FastAPI backend on port 5000..."
nohup ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 2 --env-file .env > aarkaai.log 2>&1 &

sleep 3
echo "Checking running process..."
ps aux | grep uvicorn

echo ""
echo "Testing local endpoint..."
curl -s http://127.0.0.1:5000/docs | head -n 10
echo ""
echo "AARKAAI is live on port 5000!"
