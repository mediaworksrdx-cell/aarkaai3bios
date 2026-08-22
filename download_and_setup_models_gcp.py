"""
AARKAAI – Complete Model Pipeline Downloader & LoRA Merger for GCP
Downloads:
1. rthshr/aarkaa-coder-3b-adapter + Qwen/Qwen2.5-Coder-3B-Instruct
2. rthshr/aarkaa-7b-adapter + Qwen/Qwen2.5-7B-Instruct
Merges LoRA weights and saves them into the GCP instance.
"""
import os
import sys
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login

HF_TOKEN = os.environ.get("HF_TOKEN", "")
BASE_DIR = os.path.expanduser("~/aarkaai3b")

def merge_model(base_repo: str, adapter_repo: str, output_dir: str):
    print(f"\n=======================================================")
    print(f"Processing: {adapter_repo} (Base: {base_repo})")
    print(f"Destination: {output_dir}")
    print(f"=======================================================")
    
    if os.path.exists(output_dir) and os.path.exists(os.path.join(output_dir, "model.safetensors")):
        print(f"Model already exists at {output_dir}, skipping download/merge.")
        return True

    print("[1/4] Loading base model weights in float16...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_repo,
        token=HF_TOKEN,
        torch_dtype=torch.float16,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    print(f"[2/4] Applying LoRA adapter {adapter_repo}...")
    model = PeftModel.from_pretrained(
        base_model,
        adapter_repo,
        token=HF_TOKEN,
        torch_dtype=torch.float16
    )
    print("Merging adapter into base model weights...")
    merged_model = model.merge_and_unload()

    print(f"[3/4] Saving merged model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    merged_model.save_pretrained(output_dir, safe_serialization=True)

    print("[4/4] Saving tokenizer and configs...")
    tokenizer = AutoTokenizer.from_pretrained(base_repo, token=HF_TOKEN)
    tokenizer.save_pretrained(output_dir)

    print(f"✓ Model {adapter_repo} successfully merged and saved to {output_dir}!")
    return True

def main():
    print("Starting AARKAAI 7B & Coder Model Fetch & Merge on GCP VM...")
    login(token=HF_TOKEN)

    # 1. Merge Aarkaa Coder 3B
    coder_out = os.path.join(BASE_DIR, "aarkaa-coder-3b")
    merge_model(
        base_repo="Qwen/Qwen2.5-Coder-3B-Instruct",
        adapter_repo="rthshr/aarkaa-coder-3b-adapter",
        output_dir=coder_out
    )

    # 2. Merge Aarkaa 7B
    model_7b_out = os.path.join(BASE_DIR, "aarkaa-7b")
    merge_model(
        base_repo="Qwen/Qwen2.5-7B-Instruct",
        adapter_repo="rthshr/aarkaa-7b-adapter",
        output_dir=model_7b_out
    )

    print("\n" + "=" * 60)
    print("ALL AARKAA MODELS (7B & CODER-3B) MERGED AND READY ON GCP!")
    print("=" * 60)

if __name__ == "__main__":
    main()
