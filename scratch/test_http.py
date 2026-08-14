import requests

url = "http://synthetixanalytics.com"
print(f"Querying {url}...")
try:
    res = requests.get(url, timeout=10)
    print("Status Code:", res.status_code)
    print("Content-Type:", res.headers.get("Content-Type"))
    print("Content Length:", len(res.text))
    print("First 200 characters of response:")
    print(res.text[:200])
except Exception as e:
    print("Error:", e)
