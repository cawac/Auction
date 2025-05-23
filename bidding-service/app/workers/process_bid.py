from celery import Celery

celery_app = Celery('bidding_worker', broker='redis://localhost:6379/0')

@celery_app.task
def process_bid(bid_id: int):
    # Placeholder for bid processing logic
    print(f"Processing bid with ID: {bid_id}") 