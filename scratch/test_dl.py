from huggingface_hub import snapshot_download
import sys

try:
    print("Attempting to download rthshr/aarkaa-3b from Hugging Face...")
    snapshot_download(repo_id="rthshr/aarkaa-3b", local_dir="/home/ubuntu/aarkaai3b/test_dl")
    print("Download success!")
except Exception as e:
    print("Download failed:", e)
    sys.exit(1)
