import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "aarkaai.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

for table in tables:
    print(f"Searching in table: {table}")
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        for row in rows:
            row_str = str(row)
            if "ListSkills" in row_str or "GetSkill" in row_str:
                print(f"Found match in {table}:")
                print(dict(zip(cols, row)))
    except Exception as e:
        print(f"Error reading table {table}: {e}")

conn.close()
