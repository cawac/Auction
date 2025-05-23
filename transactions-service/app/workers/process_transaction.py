# Worker to process transactions for transactions-service 
from celery import Celery

celery_app = Celery('transactions_worker', broker='redis://localhost:6379/0')

@celery_app.task
def process_transaction(transaction_id: int):
    # Placeholder for transaction processing logic
    print(f"Processing transaction with ID: {transaction_id}") 