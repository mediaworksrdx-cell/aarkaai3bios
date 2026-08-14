import json
import sys

transcript_path = r'C:\Users\daarv\.gemini\antigravity\brain\3f42ed0f-3653-4299-b215-0438d839153e\.system_generated\logs\transcript.jsonl'

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        idx = data.get('step_index', 0)
        if idx >= 1033:
            continue
        tool_calls = data.get('tool_calls', [])
        for tc in tool_calls:
            name = tc.get('name', '')
            if 'Skill' in name:
                sys.stdout.buffer.write(f"=== Step {idx} (Tool: {name}) ===\n".encode('utf-8'))
                sys.stdout.buffer.write(json.dumps(tc, indent=2).encode('utf-8'))
                sys.stdout.buffer.write(("\n" + "=" * 50 + "\n").encode('utf-8'))
