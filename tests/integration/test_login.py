import sys, urllib.request, json
sys.path.insert(0, "/home/ubuntu/aarkaai3b")

BASE = "http://127.0.0.1:5000"

def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

if __name__ == "__main__":
    try:
        status, body = post("/auth/login", {"email": "visitor@aarkaai.com", "password": "VisitorSecurePassword123!"})
        print(f"LOGIN: {status} -> {str(body)[:300]}")
    except Exception as e:
        print(f"Login failed: {e}")

