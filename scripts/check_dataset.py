import json

with open('agent_240_full_queries_and_answers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for agent, items in data.items():
    for i, it in enumerate(items):
        if it['idx'] != i + 1:
            print(f"Mismatch idx in {agent}: got {it['idx']}, expected {i+1}")
        if len(it['answer'].strip()) < 200:
            print(f"Short answer in {agent} Q{i+1}: length {len(it['answer'].strip())}")

print("Dataset integrity check done!")
