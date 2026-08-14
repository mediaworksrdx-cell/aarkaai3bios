import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "how to make briyani"
prompt, tokens, temp = engine._build_final_prompt(query, "", "general_query")

# Remove the 5 points constraint from the prompt
bad_rule = "- Limit lists or multiple points to at most 5 key points to ensure high quality and focus.\n\n"
modified_prompt = prompt.replace(bad_rule, "")

print(f"Original rule in prompt: {bad_rule in prompt}")
print(f"Modified prompt length: {len(modified_prompt)}, Tokens limit: {tokens}, Temp: {temp}")

print("\n--- Running Generation with Modified Prompt ---")
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
stream = engine._model(
    modified_prompt,
    max_tokens=tokens,
    temperature=temp,
    stop=stop_tokens,
    stream=True
)

for chunk in stream:
    token = chunk["choices"][0]["text"]
    if token:
        print(token, end="", flush=True)
print()
