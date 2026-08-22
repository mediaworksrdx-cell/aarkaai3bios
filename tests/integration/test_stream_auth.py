from database import SessionLocal, UserAccount
from modules.auth import create_access_token
import requests

db = SessionLocal()
user = db.query(UserAccount).first()
if not user:
    from modules.auth import register_user
    res = register_user("visitor@aarkaai.com", "VisitorSecurePassword123!", "Web Visitor")
    token = res["access_token"]
else:
    token = create_access_token({"sub": user.id})

print("Generated Token:", token[:20] + "...")

url = "http://127.0.0.1:5000/prompt/stream"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "query": "What is financial literacy?",
    "model_override": "aarkaa-7b"
}

r = requests.post(url, json=payload, headers=headers, stream=True)
print("Response status:", r.status_code)
for line in r.iter_lines():
    if line:
        print(line.decode('utf-8'))
        break
