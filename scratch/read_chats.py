import sqlite3
import os

db_path = '/workspace/aarkaai3b/aarkaai.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, query, response, intent, confidence, timestamp FROM conversation_history ORDER BY id DESC LIMIT 5')
        rows = cur.fetchall()
        print(f"Total chats in conversation_history: {len(rows)}")
        for row in rows:
            print("=" * 60)
            print(f"ID: {row[0]} | Timestamp: {row[5]}")
            print(f"Query: {row[1]}")
            print(f"Intent: {row[3]} (conf: {row[4]})")
            print("=" * 60)
    except Exception as e:
        print("Error reading conversation_history:", e)
        
    try:
        cur.execute('SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 10')
        rows = cur.fetchall()
        print(f"Total chats in personal_chats: {len(rows)}")
        for row in rows:
            print("=" * 60)
            print(f"ID: {row[0]} | Session: {row[1]} | Role: {row[2]}")
            print(f"Message: {row[3]}")
            print("=" * 60)
    except Exception as e:
        print("Error reading personal_chats:", e)
        
    conn.close()
else:
    print("Database not found at", db_path)
