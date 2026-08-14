import os
from pathlib import Path

BASE_DIR = Path('/home/ubuntu/aarkaai3b')
SAFE_WORK_DIR = Path(os.getenv("AARKAAI_SAFE_DIR", str(BASE_DIR / "workspace")))

print("AARKAAI_SAFE_DIR env:", os.getenv("AARKAAI_SAFE_DIR"))
print("SAFE_WORK_DIR resolved:", SAFE_WORK_DIR.resolve())
print("Does SAFE_WORK_DIR exist?", SAFE_WORK_DIR.exists())
if SAFE_WORK_DIR.exists():
    print("Files in SAFE_WORK_DIR:", os.listdir(SAFE_WORK_DIR))

# Also check env vars starting with AARKAAI
for k, v in os.environ.items():
    if k.startswith("AARKAAI"):
        print(f"  {k} = {v}")
