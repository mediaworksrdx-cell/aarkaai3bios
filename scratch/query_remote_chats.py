import sqlite3
try:
    conn = sqlite3.connect('/home/ubuntu/aarkaai3b/aarkaai.db')
    c = conn.cursor()
    c.execute('SELECT id, session_id, role, message FROM personal_chats ORDER BY id DESC LIMIT 20')
    rows = c.fetchall()
    for row in reversed(rows):
        print(f"=== ID: {row[0]} | Session: {row[1]} | Role: {row[2]} ===")
        print(row[3])
        print("=" * 80)
    conn.close()
except Exception as e:
    print(f"DB error: {e}")
