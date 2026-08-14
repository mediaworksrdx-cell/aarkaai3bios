import sqlite3

db_path = '/home/ubuntu/aarkaai3b/aarkaai.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, role, message FROM personal_chats WHERE session_id='weyhkjo1' ORDER BY id ASC")
for row in c.fetchall():
    print(f"=== {row[1].upper()} (ID: {row[0]}) ===")
    print(row[2])
    print("=" * 60)
conn.close()
