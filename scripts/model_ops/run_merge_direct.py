import os
import json
import torch
import shutil
from safetensors.torch import load_file, save_file
from huggingface_hub import hf_hub_download

HF_TOKEN = os.environ.get("HF_TOKEN", "")
BASE_DIR = os.path.expanduser("~/aarkaai3b")
OUTPUT_DIR = os.path.join(BASE_DIR, "aarkaa-7b")
ADAPTER_REPO = "rthshr/aarkaa-7b-adapter"

def main():
    print("=== Direct Shard-by-Shard 7B Merger ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("1. Downloading adapter...")
    adapter_file = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_model.safetensors", token=HF_TOKEN)
    adapter_cfg = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_config.json", token=HF_TOKEN)
    
    with open(adapter_cfg, 'r') as f:
        cfg = json.load(f)
    scale = float(cfg.get("lora_alpha", 32)) / float(cfg.get("r", 16))
    print(f"Scale: {scale}")

    lora = load_file(adapter_file)
    print(f"LoRA tensor count: {len(lora)}")

    deltas = {}
    for k in list(lora.keys()):
        if ".lora_A.weight" in k:
            bk = k.replace(".lora_A.weight", ".lora_B.weight")
            if bk in lora:
                A = lora[k].to(torch.float32)
                B = lora[bk].to(torch.float32)
                # (out_dim, r) @ (r, in_dim) -> (out_dim, in_dim)
                d = torch.matmul(B, A) * scale
                target = k.replace("base_model.model.", "").replace(".lora_A.weight", ".weight")
                deltas[target] = d

    print(f"Computed {len(deltas)} delta matrices.")

    hub_dir = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots")
    snap_name = os.listdir(hub_dir)[0]
    snap_dir = os.path.join(hub_dir, snap_name)
    print(f"Reading snapshot: {snap_dir}")

    shards = sorted([f for f in os.listdir(snap_dir) if f.startswith("model-") and f.endswith(".safetensors")])
    for s in shards:
        src = os.path.join(snap_dir, s)
        dst = os.path.join(OUTPUT_DIR, s)
        print(f"Processing shard: {s} ...")
        sd = load_file(src)
        mods = 0
        for name in list(sd.keys()):
            if name in deltas:
                orig_dt = sd[name].dtype
                merged = sd[name].to(torch.float32) + deltas[name]
                sd[name] = merged.to(orig_dt)
                mods += 1
        print(f"  Applied {mods} deltas to {s}. Writing...")
        save_file(sd, dst)
        del sd

    print("Copying configs & tokenizers...")
    for f in os.listdir(snap_dir):
        if not f.endswith(".safetensors"):
            shutil.copy2(os.path.join(snap_dir, f), os.path.join(OUTPUT_DIR, f))
            print(f"  + Copied {f}")

    print("=== 7B MERGE FINISHED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
