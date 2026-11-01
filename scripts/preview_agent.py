import json

with open("agent_240_full_queries_and_answers.json", "r", encoding="utf-8") as f:
    d = json.load(f)

fa = d["FinanceAgent"]
total_len = sum(len(it["answer"]) for it in fa)
print(f"FinanceAgent total characters: {total_len}")
for it in fa:
    print(f"[Q{it['idx']:02d}] {it['query']} ({len(it['answer'])} chars)")
