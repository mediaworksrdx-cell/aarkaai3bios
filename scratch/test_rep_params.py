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

# Test configurations
configs = [
    {"temp": 0.7, "rep_penalty": 1.0},
    {"temp": 0.7, "rep_penalty": 1.05},
    {"temp": 0.5, "rep_penalty": 1.0},
    {"temp": 0.3, "rep_penalty": 1.0},
]

for cfg in configs:
    temp = cfg["temp"]
    rp = cfg["rep_penalty"]
    print(f"\n=== TESTING temp={temp}, rep_penalty={rp} ===")
    
    stream = engine._model(
        prompt,
        max_tokens=600,
        temperature=temp,
        repeat_penalty=rp,
        top_p=0.9,
        stop=stop_tokens,
        stream=True
    )
    
    generated = []
    for chunk in stream:
        choice = chunk["choices"][0]
        token = choice["text"]
        if token:
            print(token, end="", flush=True)
            generated.append(token)
        if choice.get("finish_reason"):
            print(f"\n[Finished because: {choice['finish_reason']}]")
            break
    print()
