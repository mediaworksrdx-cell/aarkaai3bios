import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "how to make briyani"

system_prompt = (
    "You are Aarkaa AI, a highly intelligent and helpful assistant built by Synthetix Analytics.\n"
    "Provide comprehensive, detailed, and complete step-by-step guides or recipes to the user's query."
)
user_prompt = (
    f"Question: {query}\n\n"
    "Answer the question above by providing a detailed, step-by-step explanation or recipe with clear headings and sequential numbers (Step 1, Step 2, etc.). Do not truncate or summarize the steps."
)
prompt_base = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"

# Primed assistant start
primed_start = "Here is a detailed, step-by-step recipe to make delicious Biryani:\n\n"
prompt = prompt_base + primed_start

stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

print(f"=== TESTING ASSISTANT PRIMING ===")
stream = engine._model(
    prompt,
    max_tokens=1000,
    temperature=0.7,
    repeat_penalty=1.1,
    top_p=0.9,
    stop=stop_tokens,
    stream=True
)

print(primed_start, end="")
for chunk in stream:
    choice = chunk["choices"][0]
    token = choice["text"]
    if token:
        print(token, end="", flush=True)
    if choice.get("finish_reason"):
        print(f"\n[Finished because: {choice['finish_reason']}]")
        break
print()
