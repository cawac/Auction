# Notification model for notifications-service 
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class NotificationType(str, PyEnum):
    AUCTION_STARTED = "auction_started"
    NEW_BID = "new_bid"
    AUCTION_ENDED = "auction_ended"
    ITEM_SOLD = "item_sold"
    ITEM_PURCHASED = "item_purchased"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_RECEIVED = "payment_received"
    REFUND_PROCESSED = "refund_processed"
    REFUND_ISSUED = "refund_issued"

class Notification(Base):
    __tablename__ = 'notifications'
    notification_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)