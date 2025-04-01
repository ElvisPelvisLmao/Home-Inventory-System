import time
import schedule
from datetime import datetime
from inventory_service import get_inventory_items, delete_inventory_item

# Global callback variable; if set, notifications are sent via this callback.
notification_callback = None

def set_notification_callback(callback):
    global notification_callback
    notification_callback = callback

def send_notification(message):
    """Send a unified notification message via the callback or print it."""
    if notification_callback:
        notification_callback(message)
    else:
        print(f"[Notification] {message}")

def remove_stale_items():
    """
    Remove items whose expiry date is more than 7 days in the past.
    """
    today = datetime.now().date()
    stale_ids = []
    items = get_inventory_items()
    for item in items:
        expiry_date = item.expiry_date.date()
        if (today - expiry_date).days > 7:
            stale_ids.append(item.id)
    for id in stale_ids:
        delete_inventory_item(id)

def check_and_notify():
    """
    Remove stale items and then check inventory for items nearing expiry.
    Generates one unified notification message for all items within 2 days before
    or 2 days after expiry.
    """
    remove_stale_items()
    
    today = datetime.now().date()
    messages = []
    items = get_inventory_items()
    for item in items:
        expiry_date = item.expiry_date.date()
        days_before = (expiry_date - today).days
        days_after = (today - expiry_date).days
        if -2 <= days_before <= 2:
            if days_before > 0:
                messages.append(f"{item.name} ({item.quantity}{item.unit}) will expire in {days_before} day(s).")
            elif days_before == 0:
                messages.append(f"{item.name} ({item.quantity}{item.unit}) expires today!")
            elif days_after > 0 and days_after < 2:
                messages.append(f"{item.name} ({item.quantity}{item.unit}) expired {days_after} day(s) ago.")
            elif days_after >= 2:
                messages.append(f"{item.name} ({item.quantity}{item.unit}) has been spoiled!")
    if messages:
        unified_message = "\n".join(messages)
        send_notification(unified_message)

def start_notification_scheduler(interval_minutes=1440):
    """
    Start a scheduler to run the notification check every interval_minutes.
    For testing, you might use a shorter interval (e.g. 1 minute).
    """
    schedule.every(interval_minutes).minutes.do(check_and_notify)
    print("Notification scheduler started. Checking inventory regularly...")
    while True:
        schedule.run_pending()
        time.sleep(60)