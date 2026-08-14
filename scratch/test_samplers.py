import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import re
import modules.aarkaa_engine as engine

engine.init()

query = "You have 8 balls. One is heavier. Find it in 2 weighings."
prompt, _, _ = engine._build_final_prompt(query, "", "reasoning_puzzle")

stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

# 1. Test with no extra samplers
print("========================================")
print("SAMPLER OPTION 1: Only temperature=0.0")
print("========================================")
stream1 = engine._model(
    prompt,
    max_tokens=1500,
    temperature=0.0,
    stop=stop_tokens,
    stream=True
)
for chunk in stream1:
    token = chunk["choices"][0]["text"]
    if token:
        print(token, end="", flush=True)
print("\n")

# 2. Test with top_p=0.9, repeat_penalty=1.15
print("========================================")
print("SAMPLER OPTION 2: temp=0.0, top_p=0.9, repeat_penalty=1.15")
print("========================================")
stream2 = engine._model(
    prompt,
    max_tokens=1500,
    temperature=0.0,
    top_p=0.9,
    repeat_penalty=1.15,
    stop=stop_tokens,
    stream=True
)
for chunk in stream2:
    token = chunk["choices"][0]["text"]
    if token:
        print(token, end="", flush=True)
print("\n")
