"""Check server DB stats and dependencies remotely."""
import subprocess, sys

KEY = r"C:\Users\daarv\Downloads\LightsailDefaultKey-ap-south-1 (2).pem"
HOST = "ubuntu@16.170.206.243"

script = r"""
import sqlite3, sys
try:
    conn = sqlite3.connect('/home/ubuntu/aarkaai3b/aarkaai.db')
    c = conn.cursor()
    c.execute('SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 20')
    rows = c.fetchall()
    for row in reversed(rows):
        print(f"ID: {row[0]} | Session: {row[1]} | Role: {row[2]}")
        print(row[3][:500])
        print("-" * 50)
    conn.close()
except Exception as e:
    print(f"DB error: {e}")
"""

cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no",
    "-i", KEY, HOST,
    f"/home/ubuntu/aarkaai3b/venv/bin/python -c \"{script}\""
]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr)

