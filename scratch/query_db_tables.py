import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "aarkaai.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(t[0])
    # Print schema
    cursor.execute(f"PRAGMA table_info({t[0]});")
    print(cursor.fetchall())

print("\nRecent records from conversation_history (if exists):")
try:
    cursor.execute("SELECT * FROM conversation_history ORDER BY id DESC LIMIT 20;")
    cols = [d[0] for d in cursor.description]
    for row in cursor.fetchall():
        print(dict(zip(cols, row)))
except Exception as e:
    print("Error querying conversation_history:", e)

print("\nRecent records from messages (if exists):")
try:
    cursor.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 20;")
    cols = [d[0] for d in cursor.description]
    for row in cursor.fetchall():
        print(dict(zip(cols, row)))
except Exception as e:
    print("Error querying messages:", e)

conn.close()
