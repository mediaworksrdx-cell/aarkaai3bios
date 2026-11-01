import json

data = json.load(open('agent_240_full_queries_and_answers.json', encoding='utf-8'))
for q_idx in [7, 15, 18]:
    it = data['MarketingAgent'][q_idx]
    print(f"Q{it['idx']}: {it['query']}")
    print(it['answer'])
    print('---')
