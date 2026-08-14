import socket

try:
    ip = socket.gethostbyname("synthetixanalytics.com")
    print("Resolved IP for synthetixanalytics.com:", ip)
except Exception as e:
    print("DNS resolution failed:", e)

try:
    ip_www = socket.gethostbyname("www.synthetixanalytics.com")
    print("Resolved IP for www.synthetixanalytics.com:", ip_www)
except Exception as e:
    print("DNS resolution failed for www:", e)
