import sqlite3
import os

db_path = "/home/ubuntu/aarkaai3b/aarkaai.db"
if not os.path.exists(db_path):
    print("Database not found")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", tables)

for t in tables:
    table_name = t[0]
    print(f"\nSchema for table {table_name}:")
    c.execute(f"PRAGMA table_info({table_name})")
    for col in c.fetchall():
        print(f"  {col[1]} ({col[2]})")
conn.close()
