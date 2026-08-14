import sqlite3

conn = sqlite3.connect("aarkaai.db")
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables in database:")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"- {t}: {count} rows")
        
    for t in tables:
        print(f"\nSchema for {t}:")
        cursor.execute(f"PRAGMA table_info({t});")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
            
except Exception as e:
    print(f"Error: {e}")

conn.close()
