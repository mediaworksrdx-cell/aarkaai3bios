"""Test chicken tikka with no history to see why it terminates early."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import aarkaa_engine
import config

aarkaa_engine.init()

query = "how to make chicken tikka step by step"
context = ""  # No RAG candidates found for tikka

print("Building prompt...")
result = aarkaa_engine._build_final_prompt(query, context, intent="", lang="en", mode="production", history=None)
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
