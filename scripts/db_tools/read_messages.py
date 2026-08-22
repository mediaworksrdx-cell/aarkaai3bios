import sqlite3

conn = sqlite3.connect("/home/ubuntu/aarkaai3b/aarkaai.db")
cursor = conn.cursor()

try:
    cursor.execute("SELECT id, query, response FROM messages ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    for r in rows:
        print(f"=== Message ID: {r[0]} ===")
        print(f"Query: {repr(r[1])}")
        print(f"Response: {repr(r[2])}")
        print("="*40)
except Exception as e:
    print(f"Error: {e}")

conn.close()
