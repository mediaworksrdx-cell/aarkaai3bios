import sys
from llama_cpp import Llama
import os
import json

logical_cores = os.cpu_count() or 2
n_threads = logical_cores if logical_cores <= 4 else logical_cores // 2

model = Llama(
    model_path="/home/ubuntu/aarkaai3b/aarkaa-3b-q8.gguf",
    n_ctx=8192,
    n_threads=n_threads,
    n_threads_batch=n_threads,
    n_gpu_layers=0,
    verbose=False,
)

sys_prompt = "You are AARKAA, a helpful and precise AI assistant."
prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\nAnswer the following question: how to make briyani\n<|im_end|>\n<|im_start|>assistant\n"

stream = model(
    prompt,
    max_tokens=500,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.15,
    stop=["<|im_end|>", "<|im_start|>", "<|endoftext|>"],
    stream=True
)

token_count = 0
for chunk in stream:
    token_count += 1
    # print the raw chunk JSON
    print(f"Chunk {token_count}: {json.dumps(chunk)}")
print("Total tokens generated:", token_count)
