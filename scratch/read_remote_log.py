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
    "cat /workspace/aarkaai3b/aarkaai.log"
]

res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
with open("scratch/remote_log.txt", "w", encoding="utf-8") as f:
    f.write("STDOUT:\n")
    f.write(res.stdout)
    f.write("\nSTDERR:\n")
    f.write(res.stderr)
print("Log written to scratch/remote_log.txt")
