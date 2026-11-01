import json

with open('agent_240_full_queries_and_answers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for agent in data:
    print(f"=== {agent} ===")
    for i, it in enumerate(data[agent]):
        print(f"Q{i+1:02d}: {it['query']}")
    print()
