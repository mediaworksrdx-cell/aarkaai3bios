import sqlite3

conn = sqlite3.connect("aarkaai.db")
cursor = conn.cursor()

try:
    cursor.execute("SELECT id, query, response, source, timestamp FROM conversation_history ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    for r in rows:
        print(f"=== Conversation ID: {r[0]} ===")
        print(f"Query: {r[1]}")
        print(f"Source: {r[3]}")
        print(f"Response:\n{r[2]}")
        print(f"Timestamp: {r[4]}")
        print("="*40)
except Exception as e:
    print(f"Error: {e}")

conn.close()
