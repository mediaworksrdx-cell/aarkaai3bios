import os
from huggingface_hub import hf_hub_download
import json

repo_id = "rthshr/aarkaa-coder-3b-adapter"
token = os.environ.get("HF_TOKEN", "")

try:
    config_file = hf_hub_download(repo_id=repo_id, filename="adapter_config.json", token=token)
    with open(config_file, "r") as f:
        config = json.load(f)
    print("Adapter Config:")
    print(json.dumps(config, indent=2))
except Exception as e:
    print("Error:", e)
