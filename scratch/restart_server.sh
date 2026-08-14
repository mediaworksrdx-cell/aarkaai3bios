#!/bin/bash
pkill -f "uvicorn" 2>/dev/null
sleep 1
cd /workspace/aarkaai3b
python3.13 -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 >> uvicorn.log 2>&1 &
echo "Server PID: $!"
sleep 7
curl -s http://localhost:5000/health
