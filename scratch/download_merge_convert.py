import os
import shutil
import subprocess
import sys
from huggingface_hub import snapshot_download

# Configuration
token = os.environ.get("HF_TOKEN", "")
base_repo = "Qwen/Qwen2.5-Coder-3B-Instruct"
adapter_repo = "rthshr/aarkaa-coder-3b-adapter"

base_dir = "/workspace/aarkaai3b/qwen-coder-3b-base"
adapter_dir = "/workspace/aarkaai3b/aarkaa-coder-3b-adapter"
merged_dir = "/workspace/aarkaai3b/aarkaa-coder-3b-merged"
gguf_output = "/workspace/aarkaai3b/aarkaa-coder-3b-f16.gguf"

def clean_dir(path):
    if os.path.exists(path):
        print(f"Cleaning existing directory: {path}")
        shutil.rmtree(path)

try:
    # 1. Clean directories
    clean_dir(base_dir)
    clean_dir(adapter_dir)
    clean_dir(merged_dir)

    # 2. Download base model (Instruct coding base)
    print(f"\n1. Downloading base model: {base_repo}...")
    snapshot_download(
        repo_id=base_repo,
        local_dir=base_dir,
        token=token,
        ignore_patterns=["*.bin", "*.pth", "*.gguf"]  # Ignore non-safetensors formats
    )

    # 3. Download adapter
    print(f"\n2. Downloading adapter: {adapter_repo}...")
    snapshot_download(
        repo_id=adapter_repo,
        local_dir=adapter_dir,
        token=token
    )

    # 4. Merge model weights in Python
    print("\n3. Loading base model and LoRA adapter to merge...")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print("   - Loading base causal LM...")
    model = AutoModelForCausalLM.from_pretrained(
        base_dir,
        torch_dtype=torch.float16,
        device_map="cpu"
    )

    print("   - Loading adapter...")
    model = PeftModel.from_pretrained(model, adapter_dir)

    print("   - Fusing adapter parameters into base model...")
    model = model.merge_and_unload()

    print(f"   - Saving merged model to {merged_dir}...")
    model.save_pretrained(merged_dir)
    
    print("   - Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_dir)
    tokenizer.save_pretrained(merged_dir)

    # Free memory
    del model
    del tokenizer
    import gc
    gc.collect()

    # 5. Space Optimization: Delete base, adapter and cache files
    print("\n4. Cleaning intermediate folders to free disk space...")
    clean_dir(base_dir)
    clean_dir(adapter_dir)
    
    # Clean huggingface cache to prevent disk overflow
    hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
    clean_dir(hf_cache)

    # 6. Run conversion to GGUF F16
    convert_script = "/workspace/aarkaai3b/llama.cpp/convert_hf_to_gguf.py"
    print(f"\n5. Running llama.cpp conversion script to output: {gguf_output}...")
    subprocess.run([
        "python3.13", convert_script,
        merged_dir,
        "--outfile", gguf_output,
        "--outtype", "f16"
    ], check=True)

    # 7. Clean up merged model
    print("\n6. Cleaning merged model folder...")
    clean_dir(merged_dir)

    print("\n============================================================")
    print("SUCCESS: Coder model merged and converted to GGUF F16.")
    print(f"GGUF Path: {gguf_output}")
    print("============================================================")

except Exception as e:
    print(f"\nFATAL ERROR during download-merge-convert pipeline: {e}")
    sys.exit(1)
