import sqlite3

conn = sqlite3.connect("/home/ubuntu/aarkaai3b/aarkaai.db")
cursor = conn.cursor()

try:
    cursor.execute("SELECT source, COUNT(*) FROM knowledge_entries GROUP BY source")
    rows = cursor.fetchall()
    print("Knowledge entry sources:")
    for r in rows:
        print(f"Source: {r[0]} | Count: {r[1]}")
except Exception as e:
    print("Error:", e)

conn.close()
