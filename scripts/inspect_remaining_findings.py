import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('audit_findings_summary.json', 'r', encoding='utf-8') as f:
    findings = json.load(f)

for agent in ['ResearchAgent', 'CustomerSupportAgent', 'DebuggingAgent', 'CodingAgent', 'CoderAgent', 'AarkaCoderPipeline']:
    print(f"\n{'='*70}\nAGENT: {agent}\n{'='*70}")
    for it in findings.get(agent, []):
        if it['status'] != 'REVIEW':
            print(f"[{it['q_id']}] [{it['status']}/{it['severity']}] {it['title']}")
            print(f"   FINDING:    {it['finding'][:140]}")
            print(f"   CORRECTION: {it['correction'][:140]}\n")
