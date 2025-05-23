# Worker to process notifications for notifications-service 
from celery import Celery

celery_app = Celery('notifications_worker', broker='redis://localhost:6379/0')

@celery_app.task
def process_notification(notification_id: int):
    # Placeholder for notification processing logic
    print(f"Processing notification with ID: {notification_id}") 
