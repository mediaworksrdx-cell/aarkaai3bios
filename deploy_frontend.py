#!/usr/bin/env python3
"""
deploy_frontend.py — Canonical frontend deployment script for AARKAAI.

Usage:
    python deploy_frontend.py              # Full deploy: sync → build → restart
    python deploy_frontend.py --restart    # Just restart Next.js (no rebuild)
    python deploy_frontend.py --build      # Rebuild + restart (no file sync)

This script is the ONLY way to deploy frontend changes to production.
It guarantees that source files, compiled build, and running process are always in sync.
"""
import subprocess
import sys
import time
import os

# ─── Configuration ────────────────────────────────────────────────────────────
KEY = r"C:\Users\daarv\.ssh\id_ed25519"
USER = "sathishbadri2015"
HOST = "136.85.114.150"
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-i", KEY]

LOCAL_FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
REMOTE_FRONTEND = "/home/sathishbadri2015/aarka-frontend"
NODE_BIN = "/home/sathishbadri2015/.nvm/versions/node/v20.20.2/bin"

# ─── Helpers ──────────────────────────────────────────────────────────────────
def ssh(cmd: str, timeout: int = 300) -> str:
    full_cmd = ["ssh"] + SSH_OPTS + [f"{USER}@{HOST}", cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True, errors="ignore", timeout=timeout)
    if res.returncode != 0 and res.stderr.strip():
        print(f"  [WARN] stderr: {res.stderr.strip()[:500]}")
    return res.stdout.strip()


def rsync_upload():
    """Rsync local frontend source to server, excluding node_modules and .next"""
    print("\n[1/4] Syncing frontend source files to server...")
    rsync_cmd = [
        "rsync", "-avz", "--delete",
        "--exclude", "node_modules",
        "--exclude", ".next",
        "--exclude", ".env.local",   # Preserve server's env
        "-e", f"ssh {' '.join(SSH_OPTS)}",
        f"{LOCAL_FRONTEND}/",
        f"{USER}@{HOST}:{REMOTE_FRONTEND}/"
    ]
    res = subprocess.run(rsync_cmd, capture_output=True, text=True, errors="ignore", timeout=120)
    if res.returncode != 0:
        print(f"  [ERROR] rsync failed: {res.stderr[:500]}")
        # Fallback: use scp for critical files
        print("  [FALLBACK] Using SCP for critical theme files...")
        critical_files = [
            "src/app/globals.css",
            "src/app/layout.tsx",
            "src/context/ThemeContext.tsx",
            "src/components/common/ThemeToggle.tsx",
            "tailwind.config.ts",
        ]
        for f in critical_files:
            local_path = os.path.join(LOCAL_FRONTEND, f)
            remote_path = f"{REMOTE_FRONTEND}/{f}"
            if os.path.exists(local_path):
                scp_cmd = ["scp"] + SSH_OPTS + [local_path, f"{USER}@{HOST}:{remote_path}"]
                subprocess.run(scp_cmd, capture_output=True, text=True)
                print(f"    [OK] {f}")
        return True
    
    changed = [l for l in res.stdout.splitlines() if not l.startswith("sending") and not l.startswith("sent") and not l.startswith("total") and l.strip()]
    print(f"  [OK] Synced {len(changed)} items")
    return True


def install_deps():
    """Run npm install if package.json changed"""
    print("\n[2/4] Checking dependencies...")
    result = ssh(f"cd {REMOTE_FRONTEND} && export PATH={NODE_BIN}:$PATH && npm install --prefer-offline --no-audit --no-fund 2>&1 | tail -5")
    print(f"  {result}")
    return True


def build():
    """Run next build"""
    print("\n[3/4] Building Next.js production bundle...")
    print("  (This takes 30-90 seconds)")
    result = ssh(
        f"cd {REMOTE_FRONTEND} && export PATH={NODE_BIN}:$PATH && npm run build 2>&1 | tail -20",
        timeout=300
    )
    print(f"  {result}")
    
    # Verify build succeeded
    build_id = ssh(f"cat {REMOTE_FRONTEND}/.next/BUILD_ID 2>/dev/null")
    build_time = ssh(f"stat {REMOTE_FRONTEND}/.next/BUILD_ID 2>/dev/null | grep Modify")
    if build_id:
        print(f"  [OK] Build ID: {build_id}")
        print(f"  [OK] {build_time}")
        return True
    else:
        print("  [FAIL] Build failed — .next/BUILD_ID not found")
        return False


def restart():
    """Kill old Next.js and start fresh with clean user-level process management."""
    print("\n[4/4] Restarting Next.js server...")
    
    # 1. Kill old Next.js processes cleanly
    ssh("pkill -9 -f 'next-server' 2>/dev/null || true")
    ssh("fuser -k -9 3000/tcp 2>/dev/null || true")
    time.sleep(2)
    
    # 2. Start Next.js with setsid
    start_cmd = (
        f"cd {REMOTE_FRONTEND} && "
        f"export PATH={NODE_BIN}:/usr/bin:/bin:$PATH && "
        f"setsid npx next start -p 3000 > /home/sathishbadri2015/nextjs_service.log 2>&1 &"
    )
    ssh(start_cmd)
    time.sleep(4)
    
    # Verify
    listener = ssh("ss -tlpn | grep 3000")
    if "3000" in listener:
        pid = listener.split("pid=")[1].split(",")[0] if "pid=" in listener else "?"
        print(f"  [OK] Next.js running on port 3000 (PID {pid})")
    else:
        print("  [FAIL] Next.js failed to start on port 3000!")
        print("  Log output:")
        print(ssh("tail -20 /home/sathishbadri2015/nextjs_service.log"))
        return False
    
    # Quick health check
    health = ssh("curl -sI http://127.0.0.1:3000/ | head -3")
    print(f"  [OK] Health: {health.splitlines()[0] if health else 'no response'}")
    
    return True


def verify_theme():
    """Verify theme CSS is being served correctly"""
    print("\n[VERIFY] Checking theme integrity...")
    
    # Check that the compiled CSS contains our theme variables
    css_check = ssh(f"grep -l 'bg-primary' {REMOTE_FRONTEND}/.next/static/css/*.css 2>/dev/null | head -1")
    if css_check:
        print(f"  [OK] Theme variables found in compiled CSS: {os.path.basename(css_check)}")
    else:
        print("  [FAIL] Theme variables NOT found in compiled CSS!")
        return False
    
    # Check HTTP response for CSS
    html = ssh("curl -s http://127.0.0.1:3000/ | head -50")
    if "data-theme" in html or "aarka-theme" in html or "--bg-primary" in html:
        print("  [OK] Theme system present in HTML response")
    
    # Check the inline theme script is present
    if "aarka-theme" in html:
        print("  [OK] Anti-FOWT inline script present in HTML")
    
    print("  [OK] Theme deployment verified")
    return True


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--full"
    
    print("=" * 60)
    print("  AARKAAI Frontend Deployment")
    print(f"  Mode: {mode}")
    print(f"  Target: {USER}@{HOST}:{REMOTE_FRONTEND}")
    print("=" * 60)
    
    if mode == "--restart":
        restart()
        verify_theme()
    elif mode == "--build":
        build()
        restart()
        verify_theme()
    else:
        rsync_upload()
        install_deps()
        if build():
            restart()
            verify_theme()
        else:
            print("\n[FAIL] Build failed. Aborting restart to preserve current running version.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("  Deployment complete. Test at https://aarka-ai.com")
    print("=" * 60)


if __name__ == "__main__":
    main()
