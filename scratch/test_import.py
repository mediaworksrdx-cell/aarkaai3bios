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
    "cd /workspace/aarkaai3b && python3 -c 'import main'"
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
