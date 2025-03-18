import tkinter as tk
import threading
import json
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # New: DateEntry widget for calendar date selection
from models import InventoryItem
from inventory_service import add_inventory_item, get_inventory_items, delete_inventory_item
from notification_service import start_notification_scheduler, set_notification_callback, check_and_notify, remove_stale_items

# Global variables for autocomplete
COMMON_INGREDIENTS = {}   # Dictionary: ingredient name -> default unit
common_ingredients_list = []  # List of ingredient names

def load_common_ingredients():
    """Load common ingredients from JSON file."""
    global COMMON_INGREDIENTS, common_ingredients_list
    try:
        with open("common_ingredients.json", "r") as f:
            data = json.load(f)
            ingredients = data.get("ingredients", [])
            COMMON_INGREDIENTS = {item["name"]: item["default_unit"] for item in ingredients}
            common_ingredients_list = list(COMMON_INGREDIENTS.keys())
    except Exception as e:
        print("Error loading common ingredients:", e)

def update_suggestions(event):
    """Update suggestion Listbox based on text typed in entry_name."""
    text = entry_name.get().strip().lower()
    suggestion_box.delete(0, tk.END)
    if text == "":
        suggestion_box.place_forget()
        return
    # Find matches from the common ingredients list
    matches = [item for item in common_ingredients_list if text in item.lower()]
    if matches:
        # Update the Listbox height to match the number of suggestions
        suggestion_box.config(height=len(matches))
        # Place the suggestion box below the entry_name widget
        x = entry_name.winfo_x()
        y = entry_name.winfo_y() + entry_name.winfo_height()
        suggestion_box.place(x=x, y=y, width=entry_name.winfo_width())
        for match in matches:
            suggestion_box.insert(tk.END, match)
    else:
        suggestion_box.place_forget()

def on_suggestion_select(event):
    """When a suggestion is selected, fill the entry and auto-set unit."""
    if suggestion_box.curselection():
        index = suggestion_box.curselection()[0]
        selected = suggestion_box.get(index)
        entry_name.delete(0, tk.END)
        entry_name.insert(0, selected)
        if selected in COMMON_INGREDIENTS:
            unit_combobox.set(COMMON_INGREDIENTS[selected])
        suggestion_box.place_forget()

def hide_suggestions(event):
    """Hide the suggestion Listbox when focus is lost."""
    suggestion_box.place_forget()

def add_item():
    """Retrieve input values, validate them, create an InventoryItem (with unit), and add it to the DB."""
    name = entry_name.get().strip()
    quantity_str = entry_quantity.get().strip()
    # Get expiry date from the DateEntry widget as a string in the specified format
    expiry_str = entry_expiry.get_date().strftime("%Y-%m-%d")
    unit = unit_combobox.get().strip()
    
    if not name or not quantity_str or not expiry_str or not unit:
        messagebox.showerror("Error", "Please fill in all fields.")
        return
    
    try:
        quantity = int(quantity_str)
    except ValueError:
        messagebox.showerror("Error", "Quantity must be an integer.")
        return
    
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Error", "Expiry date must be in YYYY-MM-DD format.")
        return
    
    item = InventoryItem(id=None, name=name, quantity=quantity, unit=unit, expiry_date=expiry_date)
    item_id = add_inventory_item(item)
    if item_id:
        messagebox.showinfo("Success", f"Item added with ID: {item_id}")
        refresh_inventory()
    else:
        messagebox.showerror("Error", "Failed to add item.")

def refresh_inventory():
    """Remove stale items, auto-sort by expiry date, and populate the Treeview with proper tags."""
    remove_stale_items()
    for i in tree.get_children():
        tree.delete(i)
    items = sorted(get_inventory_items(), key=lambda item: item.expiry_date)
    today = datetime.now().date()
    for item in items:
        expiry_date = item.expiry_date.date()
        days_diff = (expiry_date - today).days
        tag = ""
        if days_diff < 0:
            tag = "red"      # Expired items
        elif days_diff == 0:
            tag = "green"    # Expires today
        elif 0 < days_diff <= 3:
            tag = "yellow"   # Expires within 3 days
        if tag:
            tree.insert("", "end", iid=item.id, values=(
                item.id, item.name, item.quantity, item.unit, item.expiry_date.strftime("%Y-%m-%d")
            ), tags=(tag,))
        else:
            tree.insert("", "end", iid=item.id, values=(
                item.id, item.name, item.quantity, item.unit, item.expiry_date.strftime("%Y-%m-%d")
            ))
    filter_inventory()

def delete_item():
    """Delete the selected item(s) from the inventory."""
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Please select an item to delete.")
        return
    for sel in selected:
        item_id = int(sel)
        rows_deleted = delete_inventory_item(item_id)
        if rows_deleted:
            tree.delete(sel)
            messagebox.showinfo("Deleted", f"Item with ID {item_id} deleted.")
        else:
            messagebox.showerror("Error", f"Failed to delete item with ID {item_id}.")

def filter_inventory(*args):
    """Filter inventory items based on the search query and auto-sort by expiry date."""
    query = search_entry.get().strip().lower()
    for i in tree.get_children():
        tree.delete(i)
    items = sorted(get_inventory_items(), key=lambda item: item.expiry_date)
    today = datetime.now().date()
    for item in items:
        if query in item.name.lower():
            expiry_date = item.expiry_date.date()
            days_diff = (expiry_date - today).days
            tag = ""
            if days_diff < 0:
                tag = "red"
            elif days_diff == 0:
                tag = "green"
            elif 0 < days_diff <= 3:
                tag = "yellow"
            if tag:
                tree.insert("", "end", iid=item.id, values=(
                    item.id, item.name, item.quantity, item.unit, item.expiry_date.strftime("%Y-%m-%d")
                ), tags=(tag,))
            else:
                tree.insert("", "end", iid=item.id, values=(
                    item.id, item.name, item.quantity, item.unit, item.expiry_date.strftime("%Y-%m-%d")
                ))

def run_notifications():
    """Run the notification scheduler with an immediate check after a 5-second delay."""
    import time
    time.sleep(5)
    check_and_notify()  # Immediate unified notification check on startup
    start_notification_scheduler(interval_minutes=1)

def gui_notification(message):
    """Display a unified notification pop-up in the GUI."""
    root.after(0, lambda: messagebox.showinfo("Notification", message))

def treeview_sort_column(tv, col, reverse):
    """Sort Treeview contents when a column header is clicked."""
    data_list = []
    for item in tv.get_children(''):
        value = tv.set(item, col)
        if col in ["id", "quantity"]:
            try:
                value = int(value)
            except ValueError:
                value = 0
        elif col == "expiry_date":
            try:
                value = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                value = datetime.min
        data_list.append((value, item))
    data_list.sort(key=lambda t: t[0], reverse=reverse)
    for index, (val, item) in enumerate(data_list):
        tv.move(item, '', index)
    tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

# -----------------------
# GUI Setup and Modern Styling
# -----------------------

root = tk.Tk()
root.title("Smart Household Inventory Management System")

# Apply a modern ttk theme and custom fonts
style = ttk.Style(root)
style.theme_use("clam")
style.configure("Treeview", font=("Helvetica", 10), rowheight=25)
style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))
style.map("Treeview", background=[("selected", "#347083")])
tree_tag_configs = {
    "red": {"background": "#ff4d4d"},      # Saturated red for expired items
    "green": {"background": "#00cc00"},    # Saturated green for items expiring today
    "yellow": {"background": "#ffcc00"}    # Saturated yellow for items expiring within 3 days
}

# Frames for layout organization with padding
frame_form = tk.Frame(root, padx=10, pady=10)
frame_form.pack(fill="x")
frame_buttons = tk.Frame(root, padx=10, pady=10)
frame_buttons.pack(fill="x")
frame_search = tk.Frame(root, padx=10, pady=5)
frame_search.pack(fill="x")
frame_table = tk.Frame(root, padx=10, pady=10)
frame_table.pack(fill="both", expand=True)

# Load common ingredients for autocomplete
load_common_ingredients()

# Create a Listbox for suggestions (initially hidden)
suggestion_box = tk.Listbox(root, font=("Helvetica", 10))
suggestion_box.bind("<<ListboxSelect>>", on_suggestion_select)

# Form fields for item details
tk.Label(frame_form, text="Item Name:", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_name = tk.Entry(frame_form, font=("Helvetica", 10))
entry_name.grid(row=0, column=1, padx=5, pady=5)
entry_name.bind("<KeyRelease>", update_suggestions)
entry_name.bind("<FocusOut>", hide_suggestions)

tk.Label(frame_form, text="Quantity:", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_quantity = tk.Entry(frame_form, font=("Helvetica", 10))
entry_quantity.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_form, text="Unit:", font=("Helvetica", 10)).grid(row=1, column=2, padx=5, pady=5, sticky="e")
unit_combobox = ttk.Combobox(frame_form, values=["g", "pcs"], font=("Helvetica", 10), width=5)
unit_combobox.grid(row=1, column=3, padx=5, pady=5)
unit_combobox.set("g")

tk.Label(frame_form, text="Expiry Date (YYYY-MM-DD):", font=("Helvetica", 10)).grid(row=2, column=0, padx=5, pady=5, sticky="e")
# Replace the plain Entry with a DateEntry from tkcalendar for calendar selection.
entry_expiry = DateEntry(frame_form, date_pattern="yyyy-mm-dd", font=("Helvetica", 10))
entry_expiry.grid(row=2, column=1, padx=5, pady=5)
default_date = datetime.now() + timedelta(days=3)
entry_expiry.set_date(default_date)

# Buttons for actions
btn_add = tk.Button(frame_buttons, text="Add Item", command=add_item, font=("Helvetica", 10))
btn_add.grid(row=0, column=0, padx=5, pady=5)
btn_refresh = tk.Button(frame_buttons, text="Refresh Inventory", command=refresh_inventory, font=("Helvetica", 10))
btn_refresh.grid(row=0, column=1, padx=5, pady=5)
btn_delete = tk.Button(frame_buttons, text="Delete Selected", command=delete_item, font=("Helvetica", 10))
btn_delete.grid(row=0, column=2, padx=5, pady=5)

# Search bar to filter inventory items
tk.Label(frame_search, text="Search:", font=("Helvetica", 10)).pack(side="left", padx=5)
search_entry = tk.Entry(frame_search, font=("Helvetica", 10))
search_entry.pack(side="left", padx=5)
search_entry.bind("<KeyRelease>", filter_inventory)

# Treeview widget for inventory items with sortable columns (including 'unit')
columns = ("id", "name", "quantity", "unit", "expiry_date")
tree = ttk.Treeview(frame_table, columns=columns, show="headings", selectmode="browse")
tree.heading("id", text="ID", command=lambda: treeview_sort_column(tree, "id", False))
tree.heading("name", text="Name", command=lambda: treeview_sort_column(tree, "name", False))
tree.heading("quantity", text="Quantity", command=lambda: treeview_sort_column(tree, "quantity", False))
tree.heading("unit", text="Unit", command=lambda: treeview_sort_column(tree, "unit", False))
tree.heading("expiry_date", text="Expiry Date", command=lambda: treeview_sort_column(tree, "expiry_date", False))
tree.pack(fill="both", expand=True)

# Configure tag styles for colored rows
for tag, cfg in tree_tag_configs.items():
    tree.tag_configure(tag, **cfg)

refresh_inventory()
set_notification_callback(gui_notification)
notif_thread = threading.Thread(target=run_notifications, daemon=True)
notif_thread.start()
root.mainloop()
