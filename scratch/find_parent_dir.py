import os
parent1 = r"c:\Users\daarv\.gemini\antigravity\scratch"
parent2 = r"c:\Users\daarv\.gemini\antigravity"

print("Folders in scratch:")
if os.path.exists(parent1):
    for f in os.listdir(parent1):
        if os.path.isdir(os.path.join(parent1, f)) or "synth" in f.lower():
            print(f)
print("\nFolders in antigravity:")
if os.path.exists(parent2):
    for f in os.listdir(parent2):
        if os.path.isdir(os.path.join(parent2, f)) or "synth" in f.lower():
            print(f)
