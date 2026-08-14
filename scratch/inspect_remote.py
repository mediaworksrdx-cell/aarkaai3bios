import os
import sqlite3

db_path = '/home/ubuntu/aarkaai3b/aarkaai.db'
print("Checking path:", db_path)
print("Exists:", os.path.exists(db_path))

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    print("Found rows:", len(rows))
    for row in rows:
        print(f"=== ID: {row[0]} | Session: {row[1]} | Role: {row[2]} ===")
        print(row[3][:1000])
        print("-" * 50)
    conn.close()
else:
    print("aarkaai.db not found at", db_path)
