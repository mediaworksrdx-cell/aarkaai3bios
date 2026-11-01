import json
import os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
json_path = os.path.join(root, "agent_240_full_queries_and_answers.json")
out_dir = os.path.join(root, "encyclopedia")
os.makedirs(out_dir, exist_ok=True)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for i, (agent, items) in enumerate(data.items(), 1):
    filename = f"{i:02d}_{agent}.md"
    file_path = os.path.join(out_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {agent} — Complete 20 Production Queries & Answers\n\n")
        f.write(f"*Aarka AI Technical Encyclopedia | Verified Production Knowledge Pack*\n\n")
        f.write("---\n\n")
        for it in items:
            idx = it["idx"]
            q = it["query"]
            ans = it["answer"]
            f.write(f"## [Q{idx:02d}] {q}\n\n")
            f.write(f"{ans}\n\n")
            f.write("---\n\n")
    print(f"Generated {filename} ({len(items)} queries)")
