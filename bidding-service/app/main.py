import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from .models.bid import Base, Bid
from .schemas.bid import Bid as BidSchema, BidCreate
from .workers.process_bid import process_bid
from sqlalchemy.orm import Session
from .sqlalchemy_conn import engine, get_db
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
@app.post("/bids", response_model=BidCreate, status_code=status.HTTP_201_CREATED)
def place_bid(payload: BidCreate, db: Session = Depends(get_db)):
    # Check if auction exists and is active
    try:
        auction_response = requests.get(f"http://auction-service:8000/auctions/{payload.auction_id}")
        if auction_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Auction not found or inaccessible")
        
        auction = auction_response.json()
        if auction["status"] != "Active":
            raise HTTPException(status_code=400, detail="Auction is not active")
        
        # Check if bid is higher than current price
        if payload.bid_amount <= auction["current_price"]:
            raise HTTPException(status_code=400, detail="Bid amount must be higher than current price")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating bid: {str(e)}")

    # Create new bid
    new_bid = Bid(
        auction_id=payload.auction_id,
        bidder_id=payload.bidder_id,
        bid_amount=payload.bid_amount,
        bid_time=datetime.datetime.utcnow()
    )
    db.add(new_bid)
    db.commit()
    db.refresh(new_bid)
    
    # Update auction current price
    try:
        requests.put(
            f"http://auction-service:8000/auctions/{payload.auction_id}/current_price",
            json={"current_price": payload.bid_amount}
        )
    except:
        # Log error but continue
        pass
    
    # Notify about new bid
    try:
        requests.post(
            f"http://notifications-service:8000/notifications/auction/{payload.auction_id}/bid",
            json={"bid_id": new_bid.bid_id, "bidder_id": new_bid.bidder_id, "amount": new_bid.bid_amount}
        )
    except:
        # Log error but continue
        pass
    
    return new_bid

@app.get("/bids/{bid_id}", response_model=BidSchema)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid

@app.get("/bids", response_model=list[BidSchema])
def list_bids(db: Session = Depends(get_db)):
    return db.query(Bid).all()

@app.delete("/bids/{bid_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bid(bid_id: int, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Check if the bid can be deleted (e.g., auction not ended)
    try:
        auction_response = requests.get(f"http://auction-service:8000/auctions/{bid.auction_id}")
        if auction_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Auction not found")
        
        auction = auction_response.json()
        if auction["status"] != "Active":
            raise HTTPException(status_code=400, detail="Cannot delete bid: auction is not active")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating bid deletion: {str(e)}")
    
    db.delete(bid)
    db.commit()
    return

# Specialized Operations
@app.get("/bids/auction/{auction_id}", response_model=list[BidSchema])
def get_auction_bids(auction_id: int, db: Session = Depends(get_db)):
    bids = db.query(Bid).filter(Bid.auction_id == auction_id).all()
    return bids

@app.get("/bids/user/{user_id}", response_model=list[BidSchema])
def get_user_bids(user_id: int, db: Session = Depends(get_db)):
    bids = db.query(Bid).filter(Bid.bidder_id == user_id).all()
    return bids

@app.get("/bids/auction/{auction_id}/highest", response_model=BidSchema)
def get_highest_bid(auction_id: int, db: Session = Depends(get_db)):
    highest_bid = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(Bid.bid_amount.desc()).first()
    if not highest_bid:
        raise HTTPException(status_code=404, detail="No bids found for this auction")
    return highest_bid