import sqlite3
import os

db_path = "/home/ubuntu/aarkaai3b/aarkaai.db"
if not os.path.exists(db_path):
    print("Database not found at", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 10")
for row in c.fetchall():
    print(f"ID: {row[0]} | Session: {row[1]} | Role: {row[2]}")
    print(f"Message: {row[3][:200]}...")
    print("-" * 50)
conn.close()
