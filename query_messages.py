import sqlite3

conn = sqlite3.connect("aarkaai.db")
cursor = conn.cursor()

try:
    print("=== PERSONAL CHATS ===")
    cursor.execute("SELECT id, role, message, session_id FROM personal_chats ORDER BY id ASC")
    for r in cursor.fetchall():
        print(f"ID {r[0]} ({r[1]}): {r[2][:200]}...")
        
    print("\n=== CONVERSATION HISTORY ===")
    cursor.execute("SELECT id, query, response, session_id FROM conversation_history ORDER BY id ASC")
    for r in cursor.fetchall():
        print(f"ID {r[0]}:\nQuery: {r[1][:200]}...\nResponse: {r[2][:200]}...\n")
except Exception as e:
    print(f"Error: {e}")

conn.close()
