import os
import json
import shutil
import numpy as np
from safetensors.numpy import load_file, save_file
from huggingface_hub import hf_hub_download

HF_TOKEN = os.environ.get("HF_TOKEN", "")
BASE_DIR = os.path.expanduser("~/aarkaai3b")
OUTPUT_DIR = os.path.join(BASE_DIR, "aarkaa-7b")
ADAPTER_REPO = "rthshr/aarkaa-7b-adapter"

def main():
    print("=== Pure NumPy Low-Memory 7B Merger ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[1/4] Fetching adapter...")
    adapter_file = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_model.safetensors", token=HF_TOKEN)
    adapter_cfg = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_config.json", token=HF_TOKEN)

    with open(adapter_cfg, "r") as f:
        cfg = json.load(f)
    scale = float(cfg.get("lora_alpha", 32)) / float(cfg.get("r", 16))
    print(f"  LoRA scale factor: {scale}")

    lora = load_file(adapter_file)
    print(f"  Loaded {len(lora)} adapter tensors.")

    deltas = {}
    for k in list(lora.keys()):
        if ".lora_A.weight" in k:
            bk = k.replace(".lora_A.weight", ".lora_B.weight")
            if bk in lora:
                A = lora[k].astype(np.float32)
                B = lora[bk].astype(np.float32)
                d = np.matmul(B, A) * scale
                target = k.replace("base_model.model.", "").replace(".lora_A.weight", ".weight")
                deltas[target] = d
                del A, B

    print(f"  Pre-computed {len(deltas)} delta matrices in RAM.")

    hub_dir = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots")
    snap_name = os.listdir(hub_dir)[0]
    snap_dir = os.path.join(hub_dir, snap_name)

    shards = sorted([f for f in os.listdir(snap_dir) if f.startswith("model-") and f.endswith(".safetensors")])
    for s in shards:
        src = os.path.join(snap_dir, s)
        dst = os.path.join(OUTPUT_DIR, s)
        print(f"\n[2/4] Merging shard {s}...")
        sd = load_file(src)
        mods = 0
        for name in list(sd.keys()):
            if name in deltas:
                orig_dt = sd[name].dtype
                merged = sd[name].astype(np.float32) + deltas[name]
                sd[name] = merged.astype(orig_dt)
                mods += 1
        print(f"  Applied {mods} layer adjustments. Saving shard...")
        save_file(sd, dst)
        del sd

    print("\n[3/4] Copying tokenizer & configs...")
    for f in os.listdir(snap_dir):
        if not f.endswith(".safetensors"):
            shutil.copy2(os.path.join(snap_dir, f), os.path.join(OUTPUT_DIR, f))
            print(f"  + {f}")

    print("\n=== AARKAA 7B MERGED AND SAVED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
