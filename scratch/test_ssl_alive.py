import socket
import requests

ip = "16.170.206.243"
ports = [22, 80, 443]

for port in ports:
    try:
        s = socket.create_connection((ip, port), timeout=5)
        print(f"PORT {port} is OPEN!")
        s.close()
    except Exception as e:
        print(f"PORT {port} connection failed:", e)

# Test loading via HTTPS
try:
    print("\nQuerying https://synthetixanalytics.com ...")
    res = requests.get("https://synthetixanalytics.com", timeout=10)
    print("HTTPS Status Code:", res.status_code)
    print("HTTPS Response Length:", len(res.text))
except Exception as e:
    print("HTTPS Query failed:", e)
