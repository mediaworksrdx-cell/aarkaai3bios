import os
from huggingface_hub import HfApi
import sys

token = os.environ.get('HF_TOKEN')
repo = 'rthshr/aarkaa-ai-vision'

try:
    api = HfApi(token=token)
    files = api.list_repo_files(repo)
    print("Files in repo:")
    for f in files:
        print("  -", f)
except Exception as e:
    print("Error listing repo:", e)
