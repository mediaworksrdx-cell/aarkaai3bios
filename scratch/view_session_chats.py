import sqlite3
import os

db_path = "/home/ubuntu/aarkaai3b/aarkaai.db"
if not os.path.exists(db_path):
    print("Database not found")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, role, message, timestamp FROM personal_chats WHERE session_id='test_remote_naming_session' ORDER BY id ASC")
for row in c.fetchall():
    print(f"ID: {row[0]} | Role: {row[1]} | Time: {row[3]}")
    print(f"Message: {row[2]}")
    print("-" * 80)
conn.close()
