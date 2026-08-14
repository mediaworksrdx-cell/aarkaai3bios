import requests
import json

r = requests.post(
    "http://localhost:5000/prompt",
    json={
        "prompt": "generate a premium pdf report about AI Technology Startups",
        "user_id": "test_diag"
    },
    timeout=300
)
print(f"Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2)[:1000])
