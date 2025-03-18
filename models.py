from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class InventoryItem:
    id: Optional[int]      # Assigned by the database
    name: str
    quantity: int
    unit: str              # New field: "g" for grams or "pcs" for pieces
    expiry_date: datetime

    def __post_init__(self):
        # Convert expiry_date from string to datetime if needed
        if isinstance(self.expiry_date, str):
            self.expiry_date = datetime.strptime(self.expiry_date, "%Y-%m-%d")

    def to_dict(self):
        """Helper method to convert the dataclass to a dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date.strftime("%Y-%m-%d")
        }
