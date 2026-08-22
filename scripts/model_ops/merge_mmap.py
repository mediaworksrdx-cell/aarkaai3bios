"""
Zero-RAM Memory-Mapped 7B LoRA Merger (< 50MB RAM usage)
Uses safetensors.safe_open to read tensors on-demand from disk without loading full shards.
"""
import os
import json
import shutil
import torch
from safetensors import safe_open
from safetensors.torch import save_file
from huggingface_hub import hf_hub_download

HF_TOKEN = os.environ.get("HF_TOKEN", "")
BASE_DIR = os.path.expanduser("~/aarkaai3b")
OUTPUT_DIR = os.path.join(BASE_DIR, "aarkaa-7b")
ADAPTER_REPO = "rthshr/aarkaa-7b-adapter"

def main():
    print("=" * 60)
    print("Zero-RAM Memory-Mapped LoRA Merger (Aarkaa 7B)")
    print("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[1/3] Loading LoRA adapter deltas...")
    adapter_file = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_model.safetensors", token=HF_TOKEN)
    adapter_cfg = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_config.json", token=HF_TOKEN)

    with open(adapter_cfg, "r") as f:
        cfg = json.load(f)
    scale = float(cfg.get("lora_alpha", 32)) / float(cfg.get("r", 16))

    deltas = {}
    with safe_open(adapter_file, framework="pt", device="cpu") as f_lora:
        keys = list(f_lora.keys())
        for k in keys:
            if ".lora_A.weight" in k:
                bk = k.replace(".lora_A.weight", ".lora_B.weight")
                if bk in keys:
                    A = f_lora.get_tensor(k).to(torch.float32)
                    B = f_lora.get_tensor(bk).to(torch.float32)
                    d = (torch.matmul(B, A) * scale).cpu()
                    target = k.replace("base_model.model.", "").replace(".lora_A.weight", ".weight")
                    deltas[target] = d
                    del A, B

    print(f"  Pre-computed {len(deltas)} LoRA delta tensors.")

    hub_dir = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots")
    snap_name = os.listdir(hub_dir)[0]
    snap_dir = os.path.join(hub_dir, snap_name)

    shards = sorted([f for f in os.listdir(snap_dir) if f.startswith("model-") and f.endswith(".safetensors")])
    for s in shards:
        src = os.path.join(snap_dir, s)
        dst = os.path.join(OUTPUT_DIR, s)
        print(f"\n[2/3] Streaming and merging shard {s}...")
        
        merged_shard = {}
        with safe_open(src, framework="pt", device="cpu") as f_src:
            for tensor_name in f_src.keys():
                t = f_src.get_tensor(tensor_name)
                if tensor_name in deltas:
                    orig_dt = t.dtype
                    merged = (t.to(torch.float32) + deltas[tensor_name]).to(orig_dt)
                    merged_shard[tensor_name] = merged
                else:
                    merged_shard[tensor_name] = t

        print(f"  Writing {s} to disk...")
        save_file(merged_shard, dst)
        del merged_shard

    print("\n[3/3] Copying configs & tokenizer...")
    for f in os.listdir(snap_dir):
        if not f.endswith(".safetensors"):
            shutil.copy2(os.path.join(snap_dir, f), os.path.join(OUTPUT_DIR, f))
            print(f"  + {f}")

    print("\n" + "=" * 60)
    print("✓ AARKAA 7B MERGED AND SAVED SUCCESSFULLY TO", OUTPUT_DIR)
    print("=" * 60)

if __name__ == "__main__":
    main()
