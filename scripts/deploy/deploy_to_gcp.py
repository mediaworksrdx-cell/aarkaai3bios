"""
AARKAAI – GCP Compute Engine Migration & Deployment Manager
Automates project packaging, key discovery / connection, remote upload to GCP VM (136.85.114.150),
automated environment provisioning, systemd service startup, and health checks.
"""
import os
import sys
import time
import glob
import tarfile
import subprocess

REMOTE_IP = "136.85.114.150"
POSSIBLE_USERS = ["sathishbadri2015", "ubuntu", "daarv", "debian", "admin", "rathish", "root"]
ARCHIVE_NAME = "aarkaai_gcp_deploy.tar.gz"

FILES_TO_PACK = [
    "config.py",
    "schemas.py",
    "database.py",
    "main.py",
    "pipeline.py",
    "middleware.py",
    "requirements.txt",
    "nginx_gcp.conf",
    "gcp_setup.sh",
    "start.sh",
    ".env",
    ".env.example",
    ".env.production.template",
    "orbital-heaven-504004-s2-df5a0ce91659.json",
    "migrate_add_role.py",
    "admin_db_setup.py",
    "audit_production.py",
]

DIRS_TO_PACK = [
    "modules",
    "skills",
    ".agents",
    "tests",
]

def create_archive():
    print("\n[1/5] Creating deployment package for GCP...")
    if os.path.exists(ARCHIVE_NAME):
        os.remove(ARCHIVE_NAME)

    with tarfile.open(ARCHIVE_NAME, "w:gz") as tar:
        for f in FILES_TO_PACK:
            if os.path.exists(f):
                tar.add(f, arcname=f)
                print(f"  + Added file: {f}")
            else:
                print(f"  ! Note: Optional file {f} not present")
        for d in DIRS_TO_PACK:
            if os.path.isdir(d):
                tar.add(d, arcname=d)
                print(f"  + Added dir : {d}")

    size_kb = os.path.getsize(ARCHIVE_NAME) / 1024
    print(f"-> Archive created: {ARCHIVE_NAME} ({size_kb:.1f} KB)")
    return True

def discover_ssh_auth():
    print("\n[2/5] Testing SSH credentials for GCP VM (136.85.114.150)...")
    key = r"C:\Users\daarv\.ssh\id_ed25519"
    user = "sathishbadri2015"
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        "-o", "BatchMode=yes",
        "-i", key,
        f"{user}@{REMOTE_IP}",
        "echo SSH_AUTH_OK"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    if res.returncode == 0 and "SSH_AUTH_OK" in res.stdout:
        print(f"-> Successful connection found with key: {key} (User: {user})")
        return key, user
        
    for k in glob.glob(r"C:\Users\daarv\.ssh\*.pem") + glob.glob(r"C:\Users\daarv\Downloads\*.pem"):
        for u in POSSIBLE_USERS:
            cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=3",
                "-o", "BatchMode=yes",
                "-i", k,
                f"{u}@{REMOTE_IP}",
                "echo SSH_AUTH_OK"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
            if res.returncode == 0 and "SSH_AUTH_OK" in res.stdout:
                print(f"-> Successful connection found with key: {k} (User: {u})")
                return k, u
                
    return None, None

def deploy_remote(key_path, user):
    remote_host = f"{user}@{REMOTE_IP}"
    ssh_opts = ["-o", "StrictHostKeyChecking=no", "-i", key_path]
    remote_dir = f"/home/{user}/aarkaai3b"
    
    print(f"\n[3/5] Uploading deployment package to {remote_host}:{remote_dir}...")
    # Ensure remote dir
    subprocess.run(["ssh"] + ssh_opts + [remote_host, f"mkdir -p {remote_dir}"], check=True)
    
    # Upload archive
    scp_cmd = ["scp"] + ssh_opts + [ARCHIVE_NAME, f"{remote_host}:{remote_dir}/{ARCHIVE_NAME}"]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"SCP failed: {res.stderr}")
        return False
    print("-> Archive uploaded successfully.")
    
    print(f"\n[4/5] Extracting files and running gcp_setup.sh on GCP VM...")
    remote_exec = (
        f"cd {remote_dir} && "
        f"tar -xzf {ARCHIVE_NAME} && "
        f"chmod +x gcp_setup.sh && "
        f"bash gcp_setup.sh"
    )
    res = subprocess.run(["ssh"] + ssh_opts + [remote_host, remote_exec], text=True)
    
    print(f"\n[5/5] Checking remote service status & FastAPI health...")
    health_cmd = ["ssh"] + ssh_opts + [remote_host, "curl -s http://127.0.0.1:5000/health || curl -s http://127.0.0.1:5000/docs"]
    res = subprocess.run(health_cmd, capture_output=True, text=True)
    print("Health response:", res.stdout)
    return True

def main():
    print("=" * 70)
    print("     AARKAAI GCP COMPUTE ENGINE MIGRATION & DEPLOYMENT     ")
    print(f"     Target Instance IP: {REMOTE_IP}")
    print("=" * 70)
    
    create_archive()
    
    key, user = discover_ssh_auth()
    if not key:
        print("\n" + "!" * 70)
        print("SSH Public Key is not yet authorized on the GCP VM instance.")
        print("To enable 1-click deployment from your PC:")
        print(f"1. Open GCP Console (instance-20260815-144741) -> Click 'EDIT'")
        print("2. Scroll down to 'SSH Keys' -> Click 'Add Item'")
        print("3. Paste your public key: C:\\Users\\daarv\\.ssh\\id_ed25519.pub")
        print("4. Click Save, then re-run: python deploy_to_gcp.py")
        print("\nOR, deploy instantly using GCP In-Browser SSH:")
        print("1. Click the 'SSH' button in your browser on instance-20260815-144741")
        print("2. Run the quick curl/paste setup script generated in the walkthrough.")
        print("!" * 70)
        return
        
    deploy_remote(key, user)

if __name__ == "__main__":
    main()
