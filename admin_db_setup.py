import sqlite3
import subprocess
import sys

def run_migration():
    print("Running migration script...")
    # Use sys.executable to ensure we run with the correct Python interpreter (virtualenv or system)
    result = subprocess.run([sys.executable, "migrate_add_role.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

def configure_admin():
    print("Configuring admin account...")
    conn = sqlite3.connect('aarkaai.db')
    cursor = conn.cursor()
    
    # Check if we have users (the column is 'email', not 'username')
    cursor.execute("SELECT id, email FROM users")
    users = cursor.fetchall()
    
    if not users:
        print("No users found in database to configure as admin.")
        conn.close()
        return
        
    print(f"Found {len(users)} users.")
    
    # Set the first user to admin
    first_user_id = users[0][0]
    first_user_email = users[0][1]
    
    print(f"Setting user {first_user_email} (ID: {first_user_id}) as admin...")
    cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (first_user_id,))
    conn.commit()
    
    # Verify
    cursor.execute("SELECT id, email, role FROM users WHERE id = ?", (first_user_id,))
    user = cursor.fetchone()
    print(f"Verified user role: {user}")
    
    conn.close()

if __name__ == "__main__":
    run_migration()
    configure_admin()
