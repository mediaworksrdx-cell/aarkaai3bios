import subprocess

ssh_key = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
remote_host = "ec2-user@16.170.206.243"

remote_python_code = """
import subprocess
import sqlite3

# Find all aarkaai.db files
print("Finding all aarkaai.db files on host:")
try:
    find_res = subprocess.run(["find", "/", "-name", "aarkaai.db"], capture_output=True, text=True)
    paths = [p for p in find_res.stdout.splitlines() if p]
    for path in paths:
        print(f"Found: {path}")
        try:
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM conversation_history;")
            history_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM personal_chats;")
            chats_count = c.fetchone()[0]
            print(f"  -> {path}: conversation_history={history_count}, personal_chats={chats_count}")
            conn.close()
        except Exception as e:
            print(f"  -> Error reading {path}: {e}")
except Exception as e:
    print("Find error:", e)

# Check docker containers
print("")
print("Checking running docker containers:")
try:
    docker_res = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    print(docker_res.stdout)
except Exception as e:
    print("Docker error:", e)
"""

cmd = [
    "ssh",
    "-i", ssh_key,
    "-o", "StrictHostKeyChecking=no",
    remote_host,
    "python3"
]

result = subprocess.run(cmd, input=remote_python_code, capture_output=True, text=True)
print(result.stdout)
print("STDERR:")
print(result.stderr)
