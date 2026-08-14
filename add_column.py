import sqlite3

conn = sqlite3.connect("/home/ubuntu/aarkaai3b/aarkaai.db")
cursor = conn.cursor()

try:
    # Try adding user_id column
    cursor.execute("ALTER TABLE knowledge_entries ADD COLUMN user_id VARCHAR(128)")
    conn.commit()
    print("Column user_id added successfully to knowledge_entries table!")
except Exception as e:
    # It might already exist if table was recreated
    print("Database modification status/error:", e)

conn.close()
