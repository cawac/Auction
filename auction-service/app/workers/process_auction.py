from celery import Celery

celery_app = Celery('auction_worker', broker='redis://localhost:6379/0')

@celery_app.task
def process_auction(auction_id: int):
    print(f"Processing auction with ID: {auction_id}") 