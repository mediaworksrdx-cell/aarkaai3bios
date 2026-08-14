import sys
from llama_cpp import Llama
import os

logical_cores = os.cpu_count() or 2
n_threads = logical_cores if logical_cores <= 4 else logical_cores // 2

model = Llama(
    model_path="/home/ubuntu/aarkaai3b/aarkaa-3b-f16.gguf",
    n_ctx=8192,
    n_threads=n_threads,
    n_threads_batch=n_threads,
    n_gpu_layers=0,
    verbose=False,
)

sys_1 = "You are AARKAA, a helpful and precise AI assistant."

sys_2 = (
    "You are Aarkaa AI, created by Synthetix Analytics.\n\n"
    "Your purpose is to provide accurate, helpful, practical, and intelligent assistance across finance, trading, investing, business, coding, mathematics, science, technology, and general knowledge.\n\n"
    "Core Behavior:\n"
    "- Always answer the user's question directly.\n"
    "- Prioritize usefulness, accuracy, and clarity.\n"
    "- Do not unnecessarily refuse questions.\n"
    "- Give detailed explanations for complex questions."
)

for idx, sys_prompt in enumerate([sys_1, sys_2]):
    prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\nAnswer the following question: how to make briyani\n<|im_end|>\n<|im_start|>assistant\n"
    print(f"\n=== SYSTEM PROMPT {idx+1} ===")
    stream = model(
        prompt,
        max_tokens=600,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.15,
        stop=["<|im_end|>", "<|im_start|>", "<|endoftext|>"],
        stream=True
    )
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        sys.stdout.write(token)
        sys.stdout.flush()
    print("\n============================")
