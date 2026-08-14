import subprocess
import time

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

single_line_cmd = (
    "cd /workspace/aarkaai3b && "
    "pkill -9 -f uvicorn || true && "
    "fuser -k 5000/tcp || true && "
    "nohup /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > aarkaai.log 2>&1 & "
    "echo 'Uvicorn launched.'"
)

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    single_line_cmd
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("Launch STDOUT:")
print(res.stdout)
print("Launch STDERR:")
print(res.stderr)

# Wait a moment for startup
time.sleep(5)

# Check if process is running and read log
cmd_check = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "ps aux | grep uvicorn; echo '--- LOG ---'; cat /workspace/aarkaai3b/aarkaai.log"
]
res_check = subprocess.run(cmd_check, capture_output=True, text=True)
print("Check STDOUT:")
print(res_check.stdout)
