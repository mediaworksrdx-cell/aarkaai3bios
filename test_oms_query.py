from database import SessionLocal, UserAccount
from modules.auth import create_access_token
import requests
import json

db = SessionLocal()
user = db.query(UserAccount).first()
token = create_access_token({"sub": user.id})

url = "http://127.0.0.1:5000/prompt/stream"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "query": "Design a production-ready FastAPI Order Management System (OMS) for stock trading that supports 100,000 concurrent users",
    "model_override": "aarkaa-7b"
}

print("--- TESTING STREAM RESPONSE ---")
r = requests.post(url, json=payload, headers=headers, stream=True)
count = 0
for line in r.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith("data: "):
            try:
                data = json.loads(decoded[6:])
                if data.get("type") == "content" and "token" in data:
                    print(data.get("token"), end="", flush=True)
                    count += 1
            except Exception as e:
                pass

print(f"\n\n--- STREAM COMPLETED (Total Tokens Received: {count}) ---")
