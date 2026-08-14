import subprocess
import os

keys = [
    r"C:\Users\daarv\Downloads\LightsailDefaultKey-ap-south-1 (2).pem",
    r"C:\Users\daarv\.ssh\LightsailDefaultKey-ap-south-1 (2).pem",
    r"C:\Users\daarv\.ssh\aarkaai-3b.pem",
    r"C:\Users\daarv\.ssh\marketai.pem"
]

HOST = "194.68.245.29"
PORT = 22171
USER = "root"

for key in keys:
    if not os.path.exists(key):
        print(f"Key does not exist: {key}")
        continue
    
    cmd = [
        "ssh",
        "-p", str(PORT),
        "-i", key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        f"{USER}@{HOST}",
        "echo 'Connection SUCCESS!'"
    ]
    print(f"Testing key: {key}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"===> WORKING KEY FOUND: {key}")
        print(res.stdout.strip())
        break
    else:
        print(f"Failed: {res.stderr.strip()}")
else:
    print("No working key found.")
