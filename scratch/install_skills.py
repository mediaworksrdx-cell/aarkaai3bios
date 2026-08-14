import os
import shutil
from pathlib import Path

def main():
    source_dir = Path(r"C:\Users\daarv\.gemini\antigravity\scratch\aarkaai3b\skills-main\skills-main\skills")
    dest_dir = Path(r"c:\Users\daarv\.gemini\antigravity\scratch\aarkaai3b\.agents\skills")
    
    if not source_dir.exists():
        print(f"Source directory {source_dir} does not exist.")
        return
        
    print(f"Scanning for skills in {source_dir}...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    # Walk through the source directory to find any folder containing SKILL.md
    for root, dirs, files in os.walk(source_dir):
        if "SKILL.md" in files:
            skill_source_path = Path(root)
            skill_name = skill_source_path.name
            skill_dest_path = dest_dir / skill_name
            
            print(f"Installing skill '{skill_name}' to {skill_dest_path}...")
            if skill_dest_path.exists():
                shutil.rmtree(skill_dest_path)
            shutil.copytree(skill_source_path, skill_dest_path)
            copied_count += 1
            
    print(f"Successfully installed {copied_count} custom skills to the workspace customizations root.")

if __name__ == "__main__":
    main()
