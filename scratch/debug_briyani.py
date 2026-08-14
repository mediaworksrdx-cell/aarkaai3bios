import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "how to make briyani"
prompt, tokens, temp = engine._build_final_prompt(query, "", "general_query")

print("Prompt:")
print(prompt)
print(f"Tokens: {tokens}, Temp: {temp}")

print("\n--- Running Raw Generation ---")
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
stream = engine._model(
    prompt,
    max_tokens=tokens,
    temperature=temp,
    stop=stop_tokens,
    stream=True
)

raw_tokens = []
for chunk in stream:
    token = chunk["choices"][0]["text"]
    if token:
        print(token, end="", flush=True)
        raw_tokens.append(token)
print()

raw_text = "".join(raw_tokens).strip()
cleaned_text = engine._clean_response(raw_text)

print("\n--- Cleaned Text ---")
print(cleaned_text)
