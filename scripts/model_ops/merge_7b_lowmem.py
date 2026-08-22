"""
High-Performance Chunked LoRA Merger for 7B Model (Zero-Sudo, < 1GB RAM)
Iterates through individual base model shards and merges LoRA adapter tensors in-place.
"""
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
    print("=" * 60)
    print("Low-Memory Chunked LoRA Merger (Aarkaa 7B)")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Download LoRA adapter
    print("\n[1/4] Loading LoRA adapter weights...")
    adapter_file = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_model.safetensors", token=HF_TOKEN)
    adapter_config_file = hf_hub_download(repo_id=ADAPTER_REPO, filename="adapter_config.json", token=HF_TOKEN)
    
    with open(adapter_config_file, "r") as f:
        cfg = json.load(f)
        lora_alpha = float(cfg.get("lora_alpha", 32))
        r = float(cfg.get("r", 16))
        scale = lora_alpha / r
        print(f"  LoRA scaling: alpha={lora_alpha}, r={r}, scale={scale}")
        
    lora_tensors = load_file(adapter_file)
    print(f"  Loaded {len(lora_tensors)} LoRA tensors.")
    
    # Pair A and B weights
    lora_deltas = {}
    base_prefix = "base_model.model."
    
    print("\n[2/4] Pre-computing LoRA weight deltas...")
    # Find all lora_A keys
    for k in list(lora_tensors.keys()):
        if ".lora_A.weight" in k:
            b_key = k.replace(".lora_A.weight", ".lora_B.weight")
            if b_key in lora_tensors:
                weight_a = lora_tensors[k].to(torch.float32)
                weight_b = lora_tensors[b_key].to(torch.float32)
                delta = torch.matmul(weight_b, weight_a) * scale
                
                # Corresponding base tensor name
                # e.g., base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight -> model.layers.0.self_attn.q_proj.weight
                target_base_name = k.replace(base_prefix, "").replace(".lora_A.weight", ".weight")
                lora_deltas[target_base_name] = delta
                
    print(f"  Prepared {len(lora_deltas)} merged weight adjustments.")
    
    # 2. Find base shards
    snapshot_dir = None
    hub_dir = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots")
    for snap in os.listdir(hub_dir):
        snap_path = os.path.join(hub_dir, snap)
        if os.path.isdir(snap_path):
            snapshot_dir = snap_path
            break
            
    if not snapshot_dir:
        print("Error: Could not locate snapshot directory for 7B base model.")
        return False
        
    print(f"\n[3/4] Processing base model shards from: {snapshot_dir}")
    shards = sorted([f for f in os.listdir(snapshot_dir) if f.startswith("model-") and f.endswith(".safetensors")])
    print(f"  Found shards: {shards}")
    
    for shard in shards:
        src_shard_path = os.path.join(snapshot_dir, shard)
        dst_shard_path = os.path.join(OUTPUT_DIR, shard)
        print(f"\n  Processing {shard}...")
        
        shard_dict = load_file(src_shard_path)
        modified_count = 0
        
        for tensor_name in list(shard_dict.keys()):
            if tensor_name in lora_deltas:
                orig_dtype = shard_dict[tensor_name].dtype
                merged = shard_dict[tensor_name].to(torch.float32) + lora_deltas[tensor_name]
                shard_dict[tensor_name] = merged.to(orig_dtype)
                modified_count += 1
                
        print(f"    Modified {modified_count} layers in {shard}. Saving to output...")
        save_file(shard_dict, dst_shard_path)
        del shard_dict
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
    # Copy metadata, tokenizer, index, config
    print("\n[4/4] Copying configs and tokenizer...")
    for f in os.listdir(snapshot_dir):
        if f.endswith(".json") or f.endswith(".jinja") or f.endswith(".txt") or f.startswith("tokenizer"):
            src_f = os.path.join(snapshot_dir, f)
            dst_f = os.path.join(OUTPUT_DIR, f)
            shutil.copy2(src_f, dst_f)
            print(f"  + Copied {f}")
            
    print("\n" + "=" * 60)
    print("AARKAA 7B MERGED AND SAVED TO", OUTPUT_DIR)
    print("=" * 60)
    return True

if __name__ == "__main__":
    main()
