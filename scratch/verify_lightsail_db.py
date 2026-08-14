"""Verify Lightsail DB table row counts."""
import subprocess

KEY = r"C:\Users\daarv\Downloads\LightsailDefaultKey-ap-south-1 (2).pem"
HOST = "ubuntu@16.170.206.243"

script = """
import sqlite3
db_path = '/home/ubuntu/aarkaai3b/aarkaai.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("=== Lightsail Database Tables ===")
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    conn.close()
    print("=== Done ===")
except Exception as e:
    print(f"Error: {e}")
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
