import subprocess

KEY = r"C:\Users\daarv\.ssh\id_ed25519"
USER = "sathishbadri2015"
HOST = "136.85.114.150"
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-i", KEY]

def ssh(cmd, timeout=15):
    full_cmd = ["ssh"] + SSH_OPTS + [f"{USER}@{HOST}", cmd]
    try:
        res = subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore", timeout=timeout)
        return f"STDOUT: {res.stdout.strip()}\nSTDERR: {res.stderr.strip()}\nEXIT: {res.returncode}"
    except Exception as e:
        return f"ERROR: {e}"

print("=== Checking sudo access non-interactively ===")
print(ssh("sudo -n true"))

print("\n=== Checking PM2 or Supervisor or systemd availability ===")
print(ssh("which pm2 supervisor systemctl || true"))

print("\n=== Current Running Processes on 3000 and 5000 ===")
print(ssh("ss -tlpn | grep -E '3000|5000'"))
