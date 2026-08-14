#!/bin/bash
cd /workspace/aarkaai3b

# Kill uvicorn process by process name (not full command line to avoid suicide)
pkill -9 uvicorn || true
fuser -k 5000/tcp || true

rm -f aarkaai.log
nohup /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > aarkaai.log 2>&1 &
echo "Uvicorn launched successfully."
sleep 5
cat aarkaai.log
