"""Reproduce and debug chicken tikka query on the server."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
logging.basicConfig(level=logging.INFO)

from modules import aarkaa_engine
import config

aarkaa_engine.init()

# Let's mock history to match the user's state.
# The user first asked "how to make chicken biryani step by step"
# which returned a 10-step recipe, and then asked "how to make chicken tikka step by step".
# Let's build a query with this history.

history = [
    {"role": "user", "message": "how to make chicken biryani step by step"},
    {"role": "assistant", "message": """Ingredients:
- 1 cup basmati rice
- 4 chicken pieces
- 2 potatoes
- 3 onions
- Spices

Instructions:
Step 1: Rinse the basmati rice.
Step 2: In a large pot, heat oil.
Step 3: Add cumin seeds.
Step 4: Add onions.
Step 5: Sauté potatoes.
Step 6: Add spices.
Step 7: Add chicken.
Step 8: Add potatoes back.
Step 9: Cook for 15-20 mins.
Step 10: Let rest.
Enjoy!"""}
]

query = "how to make chicken tikka step by step"
context = ""  # No RAG candidates found for tikka

print("Building prompt...")
result = aarkaa_engine._build_final_prompt(query, context, intent="", lang="en", mode="production", history=history)
prompt, tokens, temp = result[0], result[1], result[2]

print(f"Prompt length: {len(prompt)} chars")
print(f"Max tokens: {tokens}")
print(f"Temperature: {temp}")
print("--- PROMPT START ---")
print(prompt)
print("--- PROMPT END ---\n")

print("Generating stream:")
generated_text = ""
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

# Let's run llama_cpp model generation directly to inspect chunks
stream = aarkaa_engine._model(
    prompt,
    max_tokens=tokens,
    temperature=temp,
    top_p=0.9,
    repeat_penalty=1.15,
    stop=stop_tokens,
    stream=True
)

for i, chunk in enumerate(stream):
    choice = chunk["choices"][0]
    token = choice["text"]
    finish_reason = choice.get("finish_reason")
    if token:
        generated_text += token
        print(token, end="", flush=True)
    if finish_reason:
        print(f"\n[STREAM FINISHED. Reason: {finish_reason}]")

print(f"\nTotal length: {len(generated_text)} chars")
