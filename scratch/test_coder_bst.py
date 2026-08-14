import urllib.request
import json
import time

url = "http://16.170.206.243:5000/prompt"
payload = {
    "message": "Write a Python function that implements a Binary Search Tree with insert, search, and inorder traversal methods. Include time complexity comments for each method.",
    "session_id": "coder-test-001",
    "stream": False
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    url, data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

start = time.time()
print("Sending coding query to AARKA Coder 3B...")
print("=" * 60)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    elapsed = time.time() - start

    print(f"Response time : {elapsed:.2f}s")
    print(f"Model used    : {result.get('model', 'N/A')}")
    print(f"Domain routed : {result.get('domain', result.get('intent', 'N/A'))}")
    if "usage" in result:
        u = result["usage"]
        print(f"Tokens        : prompt={u.get('prompt_tokens',0)}, completion={u.get('completion_tokens',0)}")
    print()
    print("=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    # Handle different response shapes
    if "response" in result:
        print(result["response"])
    elif "choices" in result:
        print(result["choices"][0]["message"]["content"])
    else:
        print(json.dumps(result, indent=2))
except Exception as e:
    elapsed = time.time() - start
    print(f"Error after {elapsed:.2f}s: {e}")
