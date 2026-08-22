import sys
from llama_cpp import Llama

model = Llama(
    model_path="/home/ubuntu/aarkaai3b/aarkaa-3b-q8.gguf",
    n_ctx=8192,
    n_threads=4,
    verbose=False,
)

sys_prompt = "You are AARKAA, a helpful and precise AI assistant. You write detailed, thorough, and complete answers without summarizing or omitting details."
query = "Write a highly detailed, comprehensive, step-by-step recipe to make Chicken Biryani. For each step, write at least one full paragraph. Do not be concise."
prompt_str = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"

prompt_tokens = model.tokenize(prompt_str.encode("utf-8"), special=True)
print("Prompt token count:", len(prompt_tokens))

print("\n--- GENERATING WITH TOKENIZED PROMPT ---")
stream = model(
    prompt_tokens,
    max_tokens=2000,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.0,
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
