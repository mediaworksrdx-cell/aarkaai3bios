import time
import requests

BASE = "http://localhost:5000"

if __name__ == "__main__":
    # Login to get token
    try:
        login = requests.post(f"{BASE}/auth/login", json={
            "email": "visitor@aarkaai.com",
            "password": "VisitorSecurePassword123!",
            "name": "Web Visitor"
        }, timeout=5)
        token = login.json().get("access_token", "")
        print(f"Token: {token[:30]}...")
    except Exception as e:
        print(f"Connection failed: {e}")
        token = ""


    if token:
        # Send prompt
        start = time.time()
        resp = requests.post(f"{BASE}/prompt", json={
            "query": "BTC falling why?",
            "session_id": "test-session"
        }, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }, timeout=120)
        elapsed = time.time() - start

        print(f"Status: {resp.status_code}")
        print(f"Time: {elapsed:.1f}s")
        print(f"Response data:")
        res_json = resp.json()
        print("Response text:", res_json.get("response"))
        print("Sources:", res_json.get("sources"))

