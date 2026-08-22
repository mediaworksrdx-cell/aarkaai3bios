import os
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER_REPO = "rthshr/aarkaa-7b-adapter"
OUTPUT_DIR = "/home/ubuntu/aarkaa-7b-merged"

print("--- 1. Loading Base Model ---")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="cpu",
    low_cpu_mem_usage=True
)

print("--- 2. Loading Adapter & Merging ---")
model = PeftModel.from_pretrained(base_model, ADAPTER_REPO)
model = model.merge_and_unload()

print(f"--- 3. Saving Merged Model to {OUTPUT_DIR} ---")
os.makedirs(OUTPUT_DIR, exist_ok=True)
model.save_pretrained(OUTPUT_DIR, safe_serialization=True)

print("--- 4. Saving Tokenizer ---")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.save_pretrained(OUTPUT_DIR)

print("--- MERGE COMPLETE ---")
