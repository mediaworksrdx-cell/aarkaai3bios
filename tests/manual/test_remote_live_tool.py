"""
AARKAAI – Live Remote Tool Execution Test with Auth Token
Verifies live server pipeline: User -> 3B/Heuristic -> MarketDataTool -> Verified Result -> 7B Answer
"""
import requests
import json

base_url = "http://127.0.0.1:5000"

reg_payload = {
    "email": "testadmin@aarkaai.com",
    "password": "supersecurepassword123",
    "name": "Test Admin"
}

def test_live_tcs_query():
    print(f"Authenticating with {base_url}...")
    resp = requests.post(f"{base_url}/auth/login", json=reg_payload, timeout=10)
    if resp.status_code != 200:
        resp = requests.post(f"{base_url}/auth/register", json=reg_payload, timeout=10)

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Authenticated successfully. Sending live query...")

    payload = {"query": "What is the current price of TCS?"}
    try:
        resp = requests.post(f"{base_url}/prompt", json=payload, headers=headers, timeout=60)
        print("Status code:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("response", "")
            sources = data.get("sources", [])
            tool_data = data.get("tool_results", [])
            print("\n--- LIVE RESPONSE FROM PIPELINE ---")
            print(answer)
            print("-----------------------------------")
            print("Sources:", sources)
            print("Tool Results:", tool_data)
        else:
            print("Error response:", resp.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_live_tcs_query()
