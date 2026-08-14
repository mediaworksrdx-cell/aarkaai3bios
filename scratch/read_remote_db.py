import sqlite3
conn = sqlite3.connect('/home/ubuntu/aarkaai3b/aarkaai.db')
c = conn.cursor()
rows = c.execute('SELECT id, query, response, intent FROM conversation_history ORDER BY id DESC LIMIT 3').fetchall()
for r in rows:
    print(f"=== ID: {r[0]} ===")
    print(f"Query: {r[1]}")
    print(f"Intent: {r[3]}")
    print(f"Response:\n{r[2][:400]}")
    print("="*40)
