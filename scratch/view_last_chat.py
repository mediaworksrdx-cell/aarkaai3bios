import sqlite3
conn = sqlite3.connect("/home/ubuntu/aarkaai3b/aarkaai.db")
c = conn.cursor()
c.execute("SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 10")
for row in c.fetchall():
    print(row)
