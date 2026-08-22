"""
Merge Aarkaa 7B LoRA adapter with Qwen/Qwen2.5-7B-Instruct.
"""
import os
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

HF_TOKEN = os.environ.get("HF_TOKEN", "")
BASE_DIR = os.path.expanduser("~/aarkaai3b")
OUTPUT_DIR = os.path.join(BASE_DIR, "aarkaa-7b")
BASE_REPO = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER_REPO = "rthshr/aarkaa-7b-adapter"

def main():
    print("=" * 60)
    print(f"Merging {ADAPTER_REPO} into {OUTPUT_DIR}...")
    print("=" * 60)

    print("[1/4] Loading base 7B model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_REPO,
        token=HF_TOKEN,
        torch_dtype=torch.float16,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    print("[2/4] Merging LoRA adapter...")
    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER_REPO,
        token=HF_TOKEN,
        torch_dtype=torch.float16
    )
    merged_model = model.merge_and_unload()

    print(f"[3/4] Saving merged 7B model to {OUTPUT_DIR}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    merged_model.save_pretrained(OUTPUT_DIR, safe_serialization=True)

    print("[4/4] Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_REPO, token=HF_TOKEN)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("✓ AARKAA 7B MERGED AND SAVED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
