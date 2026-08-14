import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

sh_content = """#!/bin/bash
cd /workspace/aarkaai3b

# Kill uvicorn process by process name (not full command line to avoid suicide)
pkill -9 uvicorn || true
fuser -k 5000/tcp || true

rm -f aarkaai.log
nohup /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > aarkaai.log 2>&1 &
echo "Uvicorn launched successfully."
sleep 5
cat aarkaai.log
"""

# Write local script
with open("scratch/start_uvicorn.sh", "w", newline="\n") as f:
    f.write(sh_content)

# Upload the script using scp
scp_cmd = [
    "scp",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    "scratch/start_uvicorn.sh",
    f"{USER}@{HOST}:/workspace/aarkaai3b/start_uvicorn.sh"
]
subprocess.run(scp_cmd)

# Execute the script using ssh
ssh_cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "chmod +x /workspace/aarkaai3b/start_uvicorn.sh && /workspace/aarkaai3b/start_uvicorn.sh"
]

res = subprocess.run(ssh_cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
