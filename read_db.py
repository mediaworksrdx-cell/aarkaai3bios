import sqlite3

conn = sqlite3.connect("/home/ubuntu/aarkaai3b/aarkaai.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

for table in tables:
    table_name = table[0]
    print(f"\n--- {table_name} ---")
    try:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = [c[1] for c in cursor.fetchall()]
        print("Columns:", cols)
        for r in rows:
            print(dict(zip(cols, r)))
    except Exception as e:
        print(f"Error reading {table_name}: {e}")

conn.close()
