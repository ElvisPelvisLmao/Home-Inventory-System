import sqlite3
from sqlite3 import Error

DB_FILE = "inventory.db"

def create_connection(db_file=DB_FILE):
    """Create a database connection and ensure the inventory table exists."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        create_table_if_not_exists(conn)
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table_if_not_exists(conn):
    """Create the inventory table with the new unit field if it does not exist."""
    try:
        sql_create_inventory_table = """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql_create_inventory_table)
        conn.commit()
        print("Ensured inventory table exists.")
    except Error as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        print("Database connection established and table ensured.")
        conn.close()
