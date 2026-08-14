import subprocess
import time

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

commands = [
    "pkill -9 -f uvicorn || true",
    "fuser -k 5000/tcp || true",
    "rm -f /workspace/aarkaai3b/aarkaai.log",
    "ls -l /workspace/aarkaai3b/aarkaai.log || echo 'Log file successfully deleted.'",
    "nohup /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > /workspace/aarkaai3b/aarkaai.log 2>&1 &",
    "sleep 5",
    "ps aux | grep uvicorn",
    "cat /workspace/aarkaai3b/aarkaai.log"
]

cmd_str = "cd /workspace/aarkaai3b && " + " && ".join(commands)
# Wait, let's use ; instead of && to ensure everything runs even if one of the check commands returns non-zero
cmd_str = "cd /workspace/aarkaai3b; " + "; ".join(commands)

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    cmd_str
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
