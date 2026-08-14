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
prompt = engine._build_chatml(system_prompt, user_prompt)
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

print("Prompt:")
print(prompt)

stream = engine._model(prompt, max_tokens=1500, temperature=0.7, stop=stop_tokens, stream=True)
for chunk in stream:
    choice = chunk["choices"][0]
    token = choice["text"]
    finish_reason = choice.get("finish_reason")
    if token:
        print(repr(token), end=" ", flush=True)
    if finish_reason:
        print(f"\nFinished because: {finish_reason}")
