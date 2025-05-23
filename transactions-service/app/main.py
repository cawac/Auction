from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
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
        status=TransactionStatus.Pending
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

@app.put("/transactions/{transaction_id}/refund", response_model=TransactionSchema)
def process_refund(transaction_id: int, reason: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.Completed:
        raise HTTPException(status_code=400, detail="Only completed transactions can be refunded")
    
    transaction.status = TransactionStatus.Refunded
    db.commit()
    db.refresh(transaction)
    
    # Notify users about refund
    try:
        requests.post(
            "http://notifications-service:8000/notifications",
            json={
                "user_id": transaction.buyer_id,
                "type": "REFUND_PROCESSED",
                "message": f"Refund for auction #{transaction.auction_id} has been processed. Reason: {reason}",
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