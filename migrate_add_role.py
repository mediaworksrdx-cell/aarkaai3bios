"""
One-time migration: Add 'role' column to the users table.

Usage:
    python migrate_add_role.py

This adds a 'role' column with default value 'user' to existing user records.
Safe to run multiple times (idempotent).
"""
import sqlite3
import sys
from config import DB_PATH


def migrate():
    db_path = str(DB_PATH)
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if "role" in columns:
            print("[OK] Column 'role' already exists — no migration needed.")
            return

        # Add the column
        cursor.execute(
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
        )
        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "role" in columns, "Migration failed: 'role' column not found after ALTER TABLE"

        # Count affected rows
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]

        print(f"[OK] Added 'role' column to users table ({count} existing rows set to 'user')")

    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] Migration failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
