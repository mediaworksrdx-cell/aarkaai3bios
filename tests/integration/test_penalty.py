import sys
from llama_cpp import Llama
import os

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

for penalty in [1.0, 1.05, 1.1, 1.15]:
    print(f"\n=== REPEAT PENALTY {penalty} ===")
    stream = model(
        prompt,
        max_tokens=300,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=penalty,
        stop=["<|im_end|>", "<|im_start|>", "<|endoftext|>"],
        stream=True
    )
    token_count = 0
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        token_count += 1
        sys.stdout.write(token)
        sys.stdout.flush()
    print(f"\n[Generated {token_count} tokens]")
    print("============================")
