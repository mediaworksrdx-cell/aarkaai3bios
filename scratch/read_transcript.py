import json

path = r"C:\Users\daarv\.gemini\antigravity\brain\3f42ed0f-3653-4299-b215-0438d839153e\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                print(f"--- USER INPUT ---")
                print(data.get('content'))
                print("="*80)
        except Exception as e:
            pass

