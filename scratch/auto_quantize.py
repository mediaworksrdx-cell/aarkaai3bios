import os
import time
import subprocess
import sys

# Paths
base_dir = "/home/ubuntu/aarkaai3b"
quantize_bin = os.path.join(base_dir, "llama.cpp/build/bin/llama-quantize")
model_f16 = os.path.join(base_dir, "aarkaa-3b-f16.gguf")
model_q8 = os.path.join(base_dir, "aarkaa-3b-q8.gguf")

print("=== Starting Auto-Quantization Script ===")
print(f"Target quantize binary: {quantize_bin}")
print(f"Source F16 model: {model_f16} (exists: {os.path.exists(model_f16)})")

# 1. Wait for compilation to finish
compiled = False
for attempt in range(60): # 10 minutes maximum wait
    if os.path.exists(quantize_bin):
        print("llama-quantize binary found!")
        compiled = True
        break
    else:
        print(f"Waiting for compilation... attempt {attempt+1}/60")
        time.sleep(10)

if not compiled:
    print("Error: llama-quantize was not compiled within 10 minutes.")
    sys.exit(1)

# 2. Perform Quantization
print(f"Running quantization: F16 -> Q8...")
cmd = [
    quantize_bin,
    model_f16,
    model_q8,
    "q8_0"
]
print("Command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Quantization stdout:")
print(res.stdout)
print("Quantization stderr:")
print(res.stderr)

if res.returncode == 0 and os.path.exists(model_q8) and os.path.getsize(model_q8) > 1e9:
    print(f"SUCCESS: Quantized model created successfully at {model_q8}")
    print(f"Size: {os.path.getsize(model_q8) / 1e9:.2f} GB")
else:
    print("Error: Quantization failed.")
    sys.exit(1)
