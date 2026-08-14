"""Clear EC2 database chat history tables via SSH."""
import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "ec2-user@16.170.206.243"

script = """
import sqlite3
db_path = '/workspace/aarkaai3b/aarkaai.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables_to_clear = [
    "conversation_history",
    "personal_chats",
    "user_memory",
    "knowledge_entries",
    "user_knowledge_profiles",
    "rlhf_feedback",
    "user_subscriptions",
]

print("=== BEFORE ===")
for table in tables_to_clear:
    cursor.execute("SELECT COUNT(*) FROM " + table)
    print("  " + table + ": " + str(cursor.fetchone()[0]) + " rows")

for table in tables_to_clear:
    cursor.execute("DELETE FROM " + table)
    print("Cleared " + table + " (" + str(cursor.rowcount) + " rows deleted)")

conn.commit()

print("")
print("=== AFTER ===")
for table in tables_to_clear:
    cursor.execute("SELECT COUNT(*) FROM " + table)
    print("  " + table + ": " + str(cursor.fetchone()[0]) + " rows")

# Show preserved users
cursor.execute("SELECT id, email FROM users")
users = cursor.fetchall()
print("")
print("=== Preserved Users ===")
for u in users:
    print("  ID " + str(u[0]) + ": " + str(u[1]))

conn.close()
print("")
print("=== Done ===")
"""

cmd = [
    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
    "-i", KEY, HOST,
    "python3"
]
r = subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr)
