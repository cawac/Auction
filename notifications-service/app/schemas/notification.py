# Notification schema for notifications-service 
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    AUCTION_STARTED = "auction_started"
    NEW_BID = "new_bid"
    AUCTION_ENDED = "auction_ended"
    ITEM_SOLD = "item_sold"
    ITEM_PURCHASED = "item_purchased"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_RECEIVED = "payment_received"
    REFUND_PROCESSED = "refund_processed"
    REFUND_ISSUED = "refund_issued"

class NotificationBase(BaseModel):
    user_id: int
    type: NotificationType
    message: str
    metadata: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    """
    Schema for creating notifications.
    ID, timestamps, and read status are managed by the service.
    """
    pass

class Notification(NotificationBase):
    notification_id: int
    created_at: datetime
    is_read: bool = False
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True 