import requests

URL = "http://43.204.153.162:5000/rlhf"

# Payload 1: String conversation_id (like the frontend sessionId)
payload_str = {
    "user_id": "test_script",
    "rating": 1,
    "conversation_id": "1m8pw9aa",
    "correction": None
}

# Payload 2: Integer conversation_id
payload_int = {
    "user_id": "test_script",
    "rating": -1,
    "conversation_id": 1,
    "correction": "This is a correction"
}

# Payload 3: None/Null conversation_id
payload_none = {
    "user_id": "test_script",
    "rating": 1,
    "conversation_id": None,
    "correction": None
}

print("Testing Payload 1 (String ID):")
res1 = requests.post(URL, json=payload_str)
print("Status:", res1.status_code)
print("Response:", res1.json() if res1.status_code == 200 else res1.text)

print("\nTesting Payload 2 (Integer ID):")
res2 = requests.post(URL, json=payload_int)
print("Status:", res2.status_code)
print("Response:", res2.json() if res2.status_code == 200 else res2.text)

print("\nTesting Payload 3 (None ID):")
res3 = requests.post(URL, json=payload_none)
print("Status:", res3.status_code)
print("Response:", res3.json() if res3.status_code == 200 else res3.text)
