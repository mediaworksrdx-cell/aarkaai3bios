import sqlite3
conn = sqlite3.connect("aarkaai.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("=== Local Database Tables ===")
for t in sorted(tables):
    c.execute("SELECT COUNT(*) FROM " + t)
    count = c.fetchone()[0]
    print("  " + t + ": " + str(count) + " rows")
conn.close()
print("=== Done ===")
