from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .models.notification import Base, Notification, NotificationType
from .schemas.notification import Notification as NotificationSchema, NotificationCreate
from .sqlalchemy_conn import engine, get_db
import time
import logging
from sqlalchemy.sql import func


time.sleep(5)
Base.metadata.create_all(bind=engine)
app = FastAPI()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Creating database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# Basic Notification Operations
@app.post("/notifications", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    new_notification = Notification(
        user_id=notification.user_id,
        type=notification.type,
        message=notification.message,
        metadata=notification.metadata,
        created_at=datetime.utcnow(),
        is_read=False
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    
    # Note: Notification delivery would happen here in a production system
    # This could be via websockets, push notifications, email, etc.
    
    return new_notification

@app.get("/notifications/user/{user_id}", response_model=List[NotificationSchema])
def get_user_notifications(
    user_id: int, 
    unread_only: bool = False, 
    limit: int = 50, 
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifications

@app.put("/notifications/{notification_id}/read", response_model=NotificationSchema)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.notification_id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification

@app.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.notification_id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return

# Service to Service Notification Endpoints
@app.post("/notifications/auction/{auction_id}/new")
def notify_auction_event(
    auction_id: int,
    event_type: str,
    user_ids: List[int],
    message: str,
    metadata: Dict[str, Any] = None,
    db: Session = Depends(get_db)
):
    """Generic auction event notification endpoint that replaces the specific event endpoints"""
    
    try:
        notification_type = NotificationType[event_type]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid notification type: {event_type}")
    
    # Create notifications for provided users
    for user_id in user_ids:
        new_notification = Notification(
            user_id=user_id,
            type=notification_type,
            message=message,
            metadata=metadata or {"auction_id": auction_id},
            created_at=datetime.utcnow(),
            is_read=False
        )
        db.add(new_notification)
    
    db.commit()
    return {"status": "Notifications sent", "recipient_count": len(user_ids)}

@app.post("/notifications/item/{item_id}/sold")
def notify_item_sold(
    item_id: int,
    buyer_id: int,
    owner_id: int,
    db: Session = Depends(get_db)
):
    # Notify buyer
    buyer_notification = Notification(
        user_id=buyer_id,
        type=NotificationType.ITEM_PURCHASED,
        message=f"You've successfully purchased item #{item_id}",
        metadata={"item_id": item_id},
        created_at=datetime.utcnow(),
        is_read=False
    )
    db.add(buyer_notification)
    
    # Notify seller
    seller_notification = Notification(
        user_id=owner_id,
        type=NotificationType.ITEM_SOLD,
        message=f"Your item #{item_id} has been sold",
        metadata={"item_id": item_id},
        created_at=datetime.utcnow(),
        is_read=False
    )
    db.add(seller_notification)
    
    db.commit()
    return {"status": "Notifications sent"}

@app.get("/metrics")
def get_notification_metrics(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)
    one_month_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)

    total_notifications = db.query(Notification).count()
    read_count = db.query(Notification).filter(Notification.is_read == True).count()
    unread_count = db.query(Notification).filter(Notification.is_read == False).count()
    sent_today = db.query(Notification).filter(Notification.created_at >= one_day_ago).count()
    sent_week = db.query(Notification).filter(Notification.created_at >= one_week_ago).count()
    sent_month = db.query(Notification).filter(Notification.created_at >= one_month_ago).count()
    sent_year = db.query(Notification).filter(Notification.created_at >= one_year_ago).count()
    return {
        "total_notifications": total_notifications,
        "read_notifications": read_count,
        "unread_notifications": unread_count,
        "sent_today": sent_today,
        "sent_last_week": sent_week,
        "sent_last_month": sent_month,
        "sent_last_year": sent_year,
    }