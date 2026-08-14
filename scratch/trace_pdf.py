#!/usr/bin/env python3
"""
Trace the exact error when creating a PDF via AARKAAI API.
Run this on the remote server.
"""
import subprocess
import json
import sys

BASE_URL = "http://localhost:5000"

def run_curl(args):
    result = subprocess.run(["curl", "-s"] + args, capture_output=True, text=True)
    return result.stdout

# Register
reg = json.loads(run_curl(["-X", "POST", f"{BASE_URL}/auth/register",
    "-H", "Content-Type: application/json",
    "-d", '{"email":"trace999@test.com","password":"Test123!","name":"Trace"}'
]))
print("Register:", reg)
token = reg.get("access_token", "")

if not token:
    print("No token!")
    sys.exit(1)

# Send PDF creation request 
print("\nSending PDF request...")
result = run_curl(["-X", "POST", f"{BASE_URL}/prompt",
    "-H", "Content-Type: application/json",
    "-H", f"Authorization: Bearer {token}",
    "-d", '{"query":"create a pdf report about machine learning"}',
    "--max-time", "120"
])
print("Response:", result[:2000])
