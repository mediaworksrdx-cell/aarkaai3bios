import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "how to make briyani"
prompt, tokens, temp = engine._build_final_prompt(query, "", "general_query")

print(f"Prompt length: {len(prompt)}, Tokens limit: {tokens}, Temp: {temp}")

stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
stream = engine._model(
    prompt,
    max_tokens=tokens,
    temperature=temp,
    stop=stop_tokens,
    stream=True
)

for chunk in stream:
    choice = chunk["choices"][0]
    token = choice["text"]
    finish_reason = choice.get("finish_reason")
    if token:
        print(repr(token), end=" ", flush=True)
    if finish_reason:
        print(f"\nFinished because: {finish_reason}")
