"""
Download custom Aarkaa-3B GGUF weights directly to GCP VM from Hugging Face.
"""
import os
import shutil
from huggingface_hub import hf_hub_download

TOKEN = os.environ.get("HF_TOKEN", "")
REPO_ID = "rthshr/aarkaa-3b-v1"
FILENAME = "aarkaa-3b-f16.gguf"
TARGET_DIR = os.path.expanduser("~/aarkaai3b")
TARGET_PATH = os.path.join(TARGET_DIR, FILENAME)

def main():
    print("=" * 60)
    print(f"Downloading {FILENAME} (5.8 GB) from {REPO_ID} to GCP VM...")
    print("=" * 60)
    
    cached_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        token=TOKEN,
        local_dir=TARGET_DIR
    )
    print(f"\nModel downloaded successfully to: {cached_path}")
    print(f"File size: {os.path.getsize(cached_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    main()
