import subprocess
import os

dirs = {
    "aarkaai3b": r"c:\Users\daarv\.gemini\antigravity\scratch\aarkaai3b",
    "synthetix-site": r"c:\Users\daarv\.gemini\antigravity\scratch\synthetix-site"
}

for name, path in dirs.items():
    print(f"=== {name} ({path}) ===")
    if not os.path.exists(path):
        print("Directory does not exist!")
        continue
    
    # Check if .git exists
    git_dir = os.path.join(path, ".git")
    if not os.path.exists(git_dir):
        print("No .git folder found!")
        continue
        
    try:
        # Get status
        status = subprocess.run(["git", "status", "-s"], cwd=path, capture_output=True, text=True)
        print("Uncommitted changes:")
        print(status.stdout if status.stdout.strip() else "  None")
        
        # Get remotes
        remotes = subprocess.run(["git", "remote", "-v"], cwd=path, capture_output=True, text=True)
        print("Remotes:")
        print(remotes.stdout if remotes.stdout.strip() else "  None")
        
        # Get current branch
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=path, capture_output=True, text=True)
        print("Current branch:", branch.stdout.strip())
    except Exception as e:
        print("Error checking git:", e)
    print()
