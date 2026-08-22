import time
import os
from pathlib import Path
from llama_cpp import Llama

gguf = "/home/ubuntu/aarkaai3b/aarkaa-3b-q8.gguf"
print(f"Loading {gguf}...")
start_load = time.time()
model = Llama(
    model_path=gguf,
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=0,
    verbose=True
)
print(f"Loaded in {time.time() - start_load:.2f}s")

prompt = "Q: Explain Aarka AI capabilities\nA:"
print("Generating...")
start_gen = time.time()
output = model(
    prompt,
    max_tokens=50,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1
)
dur = time.time() - start_gen
print(output)
print(f"Generated in {dur:.2f}s")
