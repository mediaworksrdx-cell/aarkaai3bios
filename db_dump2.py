import sqlite3
conn = sqlite3.connect('aarkaai.db')
cur = conn.cursor()
cur.execute('SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 5')
for row in cur.fetchall():
    print(row)
