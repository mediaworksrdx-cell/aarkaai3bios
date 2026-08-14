import sqlite3

conn = sqlite3.connect("aarkaai.db")
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    for table_name_tup in tables:
        table_name = table_name_tup[0]
        print(f"\n--- Columns in {table_name} ---")
        cursor.execute(f"PRAGMA table_info({table_name});")
        print(cursor.fetchall())
        
        print(f"\n--- Sample rows in {table_name} ---")
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 3;")
        rows = cursor.fetchall()
        for r in rows:
            print(r)
except Exception as e:
    print(f"Error: {e}")

conn.close()
