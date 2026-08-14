import subprocess
import time

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

start_cmd = (
    "cd /workspace/aarkaai3b && "
    "pkill -9 -f uvicorn || true && "
    "fuser -k 5000/tcp || true && "
    "rm -f /workspace/aarkaai3b/aarkaai.log && "
    "nohup /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > /workspace/aarkaai3b/aarkaai.log 2>&1 &"
)

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    start_cmd
]

print("Launching backend server persistently...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)

print("Waiting 15 seconds for startup...")
time.sleep(15)

# Check running processes and read log file
cmd_check = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "ps aux | grep uvicorn; echo '--- LOG ---'; cat /workspace/aarkaai3b/aarkaai.log"
]
res_check = subprocess.run(cmd_check, capture_output=True, text=True)
print("Check Output:")
print(res_check.stdout)
