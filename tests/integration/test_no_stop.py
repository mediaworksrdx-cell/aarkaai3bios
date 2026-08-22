import sys
from llama_cpp import Llama
import os

model = Llama(
    model_path="/home/ubuntu/aarkaai3b/aarkaa-3b-q8.gguf",
    n_ctx=8192,
    n_threads=4,
    verbose=False,
)

sys_prompt = "You are AARKAA, a helpful and precise AI assistant."
prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\nAnswer the following question: how to make briyani\n<|im_end|>\n<|im_start|>assistant\n"

stream = model(
    prompt,
    max_tokens=300,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1,
    stop=[],
    stream=True
)

for chunk in stream:
    token = chunk["choices"][0]["text"]
    sys.stdout.write(token)
    sys.stdout.flush()
print("\nDone!")
