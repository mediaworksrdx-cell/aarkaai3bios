import json

data = json.load(open('agent_240_full_queries_and_answers.json', encoding='utf-8'))
for i, it in enumerate(data['ScreenerAgent']):
    print(f"Q{i+1:02d}: {it['query']}")
