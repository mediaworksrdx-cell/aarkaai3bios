import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

start_command = """
cd /workspace/aarkaai3b

# Kill any existing processes
pkill -9 -f "uvicorn" || true
fuser -k 5000/tcp || true

# Start application using absolute path to local uvicorn
nohup /home/ec2-user/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 > aarkaai.log 2>&1 </dev/null &
echo "Started aarkaai in background."
sleep 3
cat aarkaai.log
"""

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    start_command
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
