from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import List
from .models.transaction import Base, Transaction, TransactionStatus
from .schemas.transaction import TransactionSchema, TransactionCreate as TransactionCreateSchema, TransactionBase, TransactionStatus as TransactionStatusSchema
from .sqlalchemy_conn import engine, get_db
from .workers.process_transaction import process_transaction
import time
import requests
import logging


time.sleep(5)
Base.metadata.create_all(bind=engine)
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Creating database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# CRUD Operations
@app.post("/transactions", response_model=TransactionCreateSchema, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionCreateSchema, db: Session = Depends(get_db)):
    new_transaction = Transaction(
        auction_id=transaction.auction_id,
        buyer_id=transaction.buyer_id,
        transaction_date=datetime.utcnow(),
        status=TransactionStatus.Pending,
        amount=transaction.amount
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    # Process transaction asynchronously
    try:
        process_transaction(new_transaction.transaction_id)
    except Exception as e:
        # Log error but continue
        pass
    
    return new_transaction

@app.get("/transactions/{transaction_id}", response_model=TransactionSchema)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.get("/transactions", response_model=List[TransactionSchema])
def list_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return transactions

# Specialized Operations
@app.put("/transactions/{transaction_id}/confirm", response_model=TransactionSchema)
def confirm_payment(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.Pending:
        raise HTTPException(status_code=400, detail=f"Transaction is in {transaction.status} state, not pending")
    
    transaction.status = TransactionStatus.Completed
    db.commit()
    db.refresh(transaction)
    
    # Notify relevant services
    try:
        # Update auction status if applicable
        requests.put(f"http://auction-service:8000/auctions/{transaction.auction_id}/end")
        
        # Notify buyer
        requests.post(
            "http://notifications-service:8000/notifications",
            json={
                "user_id": transaction.buyer_id,
                "type": "PAYMENT_CONFIRMED",
                "message": f"Your payment for auction #{transaction.auction_id} has been confirmed",
                "meta": {"transaction_id": transaction.transaction_id}
            }
        )
    except:
        # Log error but continue
        pass
    
    return transaction

@app.get("/transactions/auction/{auction_id}", response_model=List[TransactionSchema])
def get_auction_transactions(auction_id: int, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.auction_id == auction_id).all()
    return transactions

@app.get("/transactions/user/{user_id}", response_model=List[TransactionSchema])
def get_user_transactions(user_id: int, db: Session = Depends(get_db)):
    # Get both buyer and seller transactions
    transactions = db.query(Transaction).filter(
        (Transaction.buyer_id == user_id) | (Transaction.seller_id == user_id)
    ).all()
    return transactions

@app.get("/metrics")
def get_payment_metrics(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)
    one_month_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)

    total_payments = db.query(Transaction).count()
    by_status = db.query(Transaction.status, func.count()).group_by(Transaction.status).all()

    # Time-based metrics
    count_day = db.query(Transaction).filter(Transaction.transaction_date >= one_day_ago).count()
    count_week = db.query(Transaction).filter(Transaction.transaction_date >= one_week_ago).count()
    count_month = db.query(Transaction).filter(Transaction.transaction_date >= one_month_ago).count()
    count_year = db.query(Transaction).filter(Transaction.transaction_date >= one_year_ago).count()

    # Amount-based metrics
    total_amount = db.query(func.coalesce(func.sum(Transaction.amount), 0)).scalar()
    avg_amount = db.query(func.coalesce(func.avg(Transaction.amount), 0)).scalar()
    min_amount = db.query(func.coalesce(func.min(Transaction.amount), 0)).scalar()
    max_amount = db.query(func.coalesce(func.max(Transaction.amount), 0)).scalar()

    # Period-based amount metrics
    amount_today = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_day_ago).scalar()
    amount_week = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_week_ago).scalar()
    amount_month = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_month_ago).scalar()
    amount_year = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_year_ago).scalar()

    avg_amount_today = db.query(func.coalesce(func.avg(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_day_ago).scalar()
    avg_amount_week = db.query(func.coalesce(func.avg(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_week_ago).scalar()
    avg_amount_month = db.query(func.coalesce(func.avg(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_month_ago).scalar()
    avg_amount_year = db.query(func.coalesce(func.avg(Transaction.amount), 0)).filter(Transaction.transaction_date >= one_year_ago).scalar()

    return {
        "total_payments": total_payments,
        "payments_today": count_day,
        "payments_last_week": count_week,
        "payments_last_month": count_month,
        "payments_last_year": count_year,
        "status_distribution": {status.value: count for status, count in by_status},
        "total_amount": total_amount,
        "avg_amount": avg_amount,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "amount_today": amount_today,
        "amount_last_week": amount_week,
        "amount_last_month": amount_month,
        "amount_last_year": amount_year,
        "avg_amount_today": avg_amount_today,
        "avg_amount_last_week": avg_amount_week,
        "avg_amount_last_month": avg_amount_month,
        "avg_amount_last_year": avg_amount_year,
    }
