import sqlite3
import os

db_path = "aarkaai.db"
if not os.path.exists(db_path):
    print("Database not found at", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
# Let's inspect the list of tables first
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", tables)

for table in tables:
    t_name = table[0]
    try:
        c.execute(f"PRAGMA table_info({t_name})")
        cols = [col[1] for col in c.fetchall()]
        print(f"Columns for {t_name}:", cols)
        
        # Select latest 10 rows
        c.execute(f"SELECT * FROM {t_name} ORDER BY rowid DESC LIMIT 10")
        rows = c.fetchall()
        print(f"Latest 10 rows from {t_name}:")
        for row in rows:
            print(str(row)[:300])
            print("=" * 30)
    except Exception as e:
        print(f"Error querying {t_name}: {e}")

conn.close()
