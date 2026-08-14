import subprocess
import os

dirs = {
    "aarkaai3b": r"c:\Users\daarv\.gemini\antigravity\scratch\aarkaai3b",
    "synthetix-site": r"c:\Users\daarv\.gemini\antigravity\scratch\synthetix-site"
}

def run_git(args, cwd):
    print(f"Running: git {' '.join(args)} in {cwd}")
    res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if res.stdout:
        print("STDOUT:", res.stdout.strip())
    if res.stderr:
        print("STDERR:", res.stderr.strip())
    return res.returncode

# ─── 1. Push aarkaai3b ────────────────────────────────────────────────────────
print("=== PUSHING aarkaai3b ===")
cwd_aarkaa = dirs["aarkaai3b"]

# Add only tracked files and our specific modified files to avoid untracked models/dbs
run_git(["add", "modules/gamma_pdf.py"], cwd_aarkaa)
run_git(["add", "scratch/test_compilation_direct.py"], cwd_aarkaa)
run_git(["add", ".agents/AGENTS.md"], cwd_aarkaa)
run_git(["add", "README.md"], cwd_aarkaa)
run_git(["add", "-u"], cwd_aarkaa) # Adds all other modified tracked files

# Commit
run_git(["commit", "-m", "Deploy premium McKinsey-style A4 PDF layout, AGENTS.md rules, and README safeguard"], cwd_aarkaa)

# Push
ret_aarkaa = run_git(["push", "origin", "main"], cwd_aarkaa)
if ret_aarkaa == 0:
    print("aarkaai3b pushed successfully!")
else:
    print("aarkaai3b push failed!")

print("\n" + "="*40 + "\n")

# ─── 2. Push synthetix-site ──────────────────────────────────────────────────
print("=== PUSHING synthetix-site ===")
cwd_site = dirs["synthetix-site"]

if os.path.exists(cwd_site):
    # Add all changes
    run_git(["add", "-A"], cwd_site)
    
    # Commit
    run_git(["commit", "-m", "Sync custom skill studio UI, route controls, and layout styles"], cwd_site)
    
    # Push
    ret_site = run_git(["push", "origin", "main"], cwd_site)
    if ret_site == 0:
        print("synthetix-site pushed successfully!")
    else:
        print("synthetix-site push failed!")
else:
    print("synthetix-site directory not found!")
