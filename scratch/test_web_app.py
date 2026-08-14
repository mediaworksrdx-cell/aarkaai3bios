import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "how to build a web app step by step"
prompt, tokens, temp = engine._build_final_prompt(query, "", "general_query")

print("Running generation for web app guide...")
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
stream = engine._model(
    prompt,
    max_tokens=1000,
    temperature=temp,
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
