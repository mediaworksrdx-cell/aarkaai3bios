import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "how to make briyani"

# Test 1: Original system prompt
system_prompt_orig = (
    "You are Aarkaa AI, a highly intelligent and helpful assistant built by Synthetix Analytics.\n"
    "Provide accurate, clear, and direct answers to the user's query."
)
user_prompt = (
    f"Question: {query}\n\n"
    "Answer the question above by providing a detailed, step-by-step explanation or recipe with clear headings and sequential numbers (Step 1, Step 2, etc.). Do not truncate or summarize the steps."
)
prompt_orig = engine._build_chatml(system_prompt_orig, user_prompt)

# Test 2: Modified system prompt
system_prompt_mod = (
    "You are Aarkaa AI, a highly intelligent and helpful assistant built by Synthetix Analytics.\n"
    "Provide comprehensive, detailed, and complete step-by-step guides or recipes to the user's query."
)
prompt_mod = engine._build_chatml(system_prompt_mod, user_prompt)

stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

print("=== RUNNING ORIGINAL SYSTEM PROMPT ===")
stream = engine._model(prompt_orig, max_tokens=1500, temperature=0.7, stop=stop_tokens, stream=True)
for chunk in stream:
    token = chunk["choices"][0]["text"]
    if token:
        print(token, end="", flush=True)
print("\n")

print("=== RUNNING MODIFIED SYSTEM PROMPT ===")
stream = engine._model(prompt_mod, max_tokens=1500, temperature=0.7, stop=stop_tokens, stream=True)
for chunk in stream:
    token = chunk["choices"][0]["text"]
    if token:
        print(token, end="", flush=True)
print("\n")
