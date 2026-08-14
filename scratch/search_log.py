import json
import sys

transcript_path = r'C:\Users\daarv\.gemini\antigravity\brain\3f42ed0f-3653-4299-b215-0438d839153e\.system_generated\logs\transcript.jsonl'

user_messages = []
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            user_messages.append(data)

# Print the last 15 user messages
for msg in user_messages[-15:]:
    sys.stdout.buffer.write(f"=== User Step {msg.get('step_index')} ===\n".encode('utf-8'))
    sys.stdout.buffer.write((msg.get('content', '') + "\n").encode('utf-8'))
    sys.stdout.buffer.write(("-" * 50 + "\n").encode('utf-8'))
