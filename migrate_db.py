import sqlite3

db_path = "aarkaai.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(knowledge_entries);")
    cols = [col[1] for col in cursor.fetchall()]
    print("Existing columns in knowledge_entries:", cols)
    if "user_id" not in cols:
        cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN user_id VARCHAR(128)")
        conn.commit()
        print("Column user_id added successfully to knowledge_entries table!")
    else:
        print("Column user_id already exists.")
except Exception as e:
    print("Migration failed:", e)
finally:
    conn.close()
