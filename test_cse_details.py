import urllib.request
import urllib.parse
import json
import config

api_key = config.GOOGLE_CSE_API_KEY
cse_id = config.GOOGLE_CSE_ID

params = urllib.parse.urlencode({
    "key": api_key,
    "cx": cse_id,
    "q": "latest AI news today",
    "num": 3,
})
url = f"https://www.googleapis.com/customsearch/v1?{params}"
print("Testing URL without sort=date parameter...")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "AARKAAI/2.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    items = data.get("items", [])
    print(f"SUCCESS! Found {len(items)} items:")
    for item in items[:3]:
        print("-", item.get("title"), "-->", item.get("link"))
except Exception as e:
    print("FAILED:", e)
    if hasattr(e, "read"):
        print("Body:", e.read().decode("utf-8"))
