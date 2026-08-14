"""Verify EC2 DB table row counts via SSH stdin pipe."""
import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "ec2-user@16.170.206.243"

script = """
import sqlite3
db_path = '/workspace/aarkaai3b/aarkaai.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("=== EC2 Database Tables ===")
    for table in sorted(tables):
        cursor.execute("SELECT COUNT(*) FROM " + table)
        count = cursor.fetchone()[0]
        print("  " + table + ": " + str(count) + " rows")
    conn.close()
    print("=== Done ===")
except Exception as e:
    print("Error: " + str(e))
"""

cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
    "-i", KEY, HOST,
    "python3"
]
r = subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr)
