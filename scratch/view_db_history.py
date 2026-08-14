import sqlite3
import os

db_path = "/home/ubuntu/aarkaai3b/aarkaai.db"
if not os.path.exists(db_path):
    print("Database not found")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, session_id, query, response, intent, confidence, source, timestamp FROM conversation_history ORDER BY id DESC LIMIT 10")
for row in c.fetchall():
    print(f"ID: {row[0]} | Session: {row[1]} | Intent: {row[4]} | Confidence: {row[5]}")
    print(f"Query: {row[2]}")
    print(f"Response: {row[3]}")
    print("-" * 80)
conn.close()
