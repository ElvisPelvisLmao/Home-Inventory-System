import sqlite3
from datetime import datetime, timedelta
from database import create_connection
from models import InventoryItem

def add_inventory_item(item: InventoryItem):
    """Insert a new inventory item into the database, including the unit."""
    conn = create_connection()
    sql = """
    INSERT INTO inventory (name, quantity, unit, expiry_date)
    VALUES (?, ?, ?, ?)
    """
    try:
        cur = conn.cursor()
        cur.execute(sql, (item.name, item.quantity, item.unit, item.expiry_date.strftime("%Y-%m-%d")))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding item: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_inventory_items():
    """Retrieve all inventory items from the database."""
    conn = create_connection()
    sql = "SELECT id, name, quantity, unit, expiry_date FROM inventory"
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        items = []
        for row in rows:
            # row: (id, name, quantity, unit, expiry_date)
            item = InventoryItem(id=row[0], name=row[1], quantity=row[2], unit=row[3], expiry_date=row[4])
            items.append(item)
        return items
    except sqlite3.Error as e:
        print(f"Error fetching items: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_inventory_item(item_id: int):
    """Delete an inventory item by ID."""
    conn = create_connection()
    sql = "DELETE FROM inventory WHERE id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (item_id,))
        conn.commit()
        return cur.rowcount
    except sqlite3.Error as e:
        print(f"Error deleting item: {e}")
        return None
    finally:
        if conn:
            conn.close()
