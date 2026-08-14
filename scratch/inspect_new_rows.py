import sqlite3

db_path = '/home/ubuntu/aarkaai3b/aarkaai.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, session_id, role, message FROM personal_chats WHERE id > 980 ORDER BY id ASC")
for row in c.fetchall():
    print(f"=== ID: {row[0]} | Session: {row[1]} | Role: {row[2]} ===")
    print(row[3])
    print("=" * 60)
conn.close()
