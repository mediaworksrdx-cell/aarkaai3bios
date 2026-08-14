import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

debug_command = """
cd /workspace/aarkaai3b
pkill -9 -f "uvicorn" || true
fuser -k 5000/tcp || true
timeout 5 /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
"""

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    debug_command
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
