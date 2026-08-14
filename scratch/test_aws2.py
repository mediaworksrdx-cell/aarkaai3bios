import subprocess
import os

keys = [
    r"C:\Users\daarv\Downloads\aarkaai.pem",
    r"C:\Users\daarv\Downloads\aarkaai3b.pem",
]
HOST = "16.170.206.243"
users = ["ubuntu", "ec2-user", "admin", "root", "debian"]

for key in keys:
    if not os.path.exists(key):
        print(f"Key does not exist: {key}")
        continue
    for user in users:
        cmd = [
            "ssh",
            "-i", key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            f"{user}@{HOST}",
            "echo 'SUCCESS'"
        ]
        print(f"Testing {user}@{HOST} with key: {os.path.basename(key)}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"===> WORKING COMBINATION FOUND: User={user}, Key={key}")
            print(res.stdout.strip())
            exit(0)
        else:
            print(f"Failed: {res.stderr.strip() or res.stdout.strip()}")
print("Finished testing combinations.")
