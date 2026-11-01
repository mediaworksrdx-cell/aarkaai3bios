import json
with open('agent_240_full_queries_and_answers.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
print("=== MarketingAgent ===")
for it in d['MarketingAgent']:
    print(f"Q{it['idx']:02d}: {it['query']}")
print("\n=== DebuggingAgent ===")
for it in d['DebuggingAgent']:
    print(f"Q{it['idx']:02d}: {it['query']}")
