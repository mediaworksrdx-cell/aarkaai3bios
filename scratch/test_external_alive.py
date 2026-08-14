import requests

print("Testing external connectivity to Nginx (Port 80)...")
try:
    res = requests.get("http://16.170.206.243", timeout=10)
    print("Nginx Status:", res.status_code)
    print("Nginx Response Length:", len(res.text))
    print("First 200 chars:")
    print(res.text[:200])
except Exception as e:
    print("Nginx Error:", e)

print("\nTesting external connectivity to Backend API (Port 5000)...")
try:
    res_api = requests.get("http://16.170.206.243:5000/health", timeout=10)
    print("API Status:", res_api.status_code)
    print("API Response JSON:", res_api.json())
except Exception as e:
    print("API Error:", e)
