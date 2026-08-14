import subprocess
import os

keys = [
    r"C:\Users\daarv\Downloads\LightsailDefaultKey-ap-south-1 (2).pem",
    r"C:\Users\daarv\.ssh\LightsailDefaultKey-ap-south-1 (2).pem",
    r"C:\Users\daarv\.ssh\aarkaai-3b.pem",
    r"C:\Users\daarv\.ssh\marketai.pem"
]

HOST = "194.68.245.29"
ports = [22, 22168]
USER = "root"

for port in ports:
    for key in keys:
        if not os.path.exists(key):
            continue
        
        cmd = [
            "ssh",
            "-p", str(port),
            "-i", key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            f"{USER}@{HOST}",
            "echo 'SUCCESS'"
        ]
        print(f"Testing port {port} with key: {os.path.basename(key)}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"===> WORKING COMBINATION FOUND: Port={port}, Key={key}")
            print(res.stdout.strip())
            exit(0)
        else:
            print(f"Failed: {res.stderr.strip() or res.stdout.strip()}")

print("No working combination found.")
