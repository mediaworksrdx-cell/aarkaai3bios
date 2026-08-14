import sqlite3
conn = sqlite3.connect('aarkaai.db')
c = conn.cursor()
c.execute("SELECT * FROM personal_chats WHERE message LIKE '%Bonjour%'")
print('Personal chats Bonjour:', c.fetchall())
c.execute("SELECT * FROM conversation_history WHERE response LIKE '%Bonjour%'")
print('Conv history Bonjour:', c.fetchall())
conn.close()
