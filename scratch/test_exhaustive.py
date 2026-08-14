import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "explain how quantum computing works in detail"

system_prompt = (
    "You are Aarkaa AI, a highly intelligent and helpful assistant built by Synthetix Analytics. "
    "You must provide detailed, comprehensive, and exhaustive answers to the user's questions, explaining concepts thoroughly and providing step-by-step guides with all details. Do not summarize or provide short answers."
)
prompt = engine._build_chatml(system_prompt, f"Question: {query}\n\nProvide an exhaustive, detailed, and comprehensive explanation of how quantum computing works.")
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

print("Running generation for quantum computing (exhaustive)...")
stream = engine._model(
    prompt,
    max_tokens=1000,
    temperature=0.7,
    stop=stop_tokens,
    stream=True
)

for chunk in stream:
    choice = chunk["choices"][0]
    token = choice["text"]
    if token:
        print(token, end="", flush=True)
    if choice.get("finish_reason"):
        print(f"\n[Finished because: {choice['finish_reason']}]")
        break
print()
