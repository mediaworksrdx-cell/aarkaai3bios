import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "cd /workspace/aarkaai3b && /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000"
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)
except subprocess.TimeoutExpired as e:
    print("TIMEOUT REACHED!")
    print("STDOUT SO FAR:")
    print(e.stdout if e.stdout else "")
    print("STDERR SO FAR:")
    print(e.stderr if e.stderr else "")
