import socket
import sys

ip = "16.170.206.243"
port = 22

try:
    print(f"Testing TCP connection to {ip}:{port}...")
    s = socket.create_connection((ip, port), timeout=5)
    print("PORT 22 is OPEN!")
    s.close()
except Exception as e:
    print("PORT 22 connection failed:", e)

try:
    print("Testing TCP connection to port 80...")
    s = socket.create_connection((ip, 80), timeout=5)
    print("PORT 80 is OPEN!")
    s.close()
except Exception as e:
    print("PORT 80 connection failed:", e)
