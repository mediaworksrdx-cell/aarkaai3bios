import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_data(user_id: int, name: str = None, db_path: str = "example.db"):
    """
    Inserts a user record into the SQLite database with robust unique constraint handling.
    
    Args:
        user_id (int): The unique identifier for the user.
        name (str, optional): The name of the user. Defaults to None.
        db_path (str): Path to the SQLite database file.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # Enable write-ahead logging (WAL) for better concurrent performance
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        
        cursor = conn.cursor()
        
        # Ensure the table schema is initialized with a PRIMARY KEY constraint
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT)"
        )
        conn.commit()
        
        # Insert record using parameterized query to prevent SQL injection
        query = "INSERT INTO users (user_id, name) VALUES (?, ?)"
        cursor.execute(query, (user_id, name))
        conn.commit()
        logger.info("Successfully inserted user_id %d", user_id)
        
    except sqlite3.IntegrityError as e:
        if conn:
            conn.rollback()
        logger.warning("IntegrityError: User ID %d already exists. Transaction rolled back. Details: %s", user_id, e)
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Database error occurred: %s", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Test insertion flow
    insert_data(1, "Alpha User")
    # Test duplicate insertion handling
    insert_data(1, "Beta User")
