import json

with open("agent_240_full_queries_and_answers.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for it in d["CoderAgent"]:
    print(f"Coder Q{it['idx']:02d}: {it['query']}")
