import modules.aarkaa_engine as engine

engine.init()

query = """What is the output?

def test():
    x = [1, 2, 3]
    y = x
    y.append(4)
    print(x)

test()"""

# Simulate build final prompt with is_code=True
result = engine._build_final_prompt(query, context="", intent="coding_help", lang="en", mode="production", history=None)
prompt, tokens, temp = result[0], result[1], result[2]

print("--- PROMPT ---")
print(prompt)
print("--- TEMP ---", temp)
print("--- GENERATING ---")
response = engine._generate(prompt, max_new_tokens=tokens, temperature=temp)
print("--- RESPONSE ---")
print(response)
