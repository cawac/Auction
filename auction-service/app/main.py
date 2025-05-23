from fastapi import FastAPI, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from .models.auction import Base, Auction as AuctionModel, AuctionStatus
from .schemas.auction import Auction as AuctionSchema, AuctionStatus as AuctionStatusSchema, AuctionCreate
from .sqlalchemy_conn import engine, get_db
from .workers.process_auction import process_auction
import time
import requests
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

time.sleep(5)
app = FastAPI()

logger.info("Creating database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# CRUD Operations
@app.post("/auctions", response_model=AuctionSchema, status_code=status.HTTP_201_CREATED)
def create_auction(payload: AuctionCreate, db: Session = Depends(get_db)):
    new_auc = AuctionModel(
        item_id=payload.item_id,
        start_time=payload.start_time,
        end_date=payload.end_date,
        starting_price=payload.starting_price,
        current_price=payload.current_price,
        status=payload.status
    )
    db.add(new_auc)
    db.commit()
    db.refresh(new_auc)
    return new_auc

@app.get("/auctions/{auction_id}", response_model=AuctionSchema)
def get_auction(auction_id: int, db: Session = Depends(get_db)):
    auction = db.query(AuctionModel).filter(AuctionModel.auction_id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction

@app.get("/auctions", response_model=List[AuctionSchema])
def list_auctions(db: Session = Depends(get_db)):
    auctions = db.query(AuctionModel).all()
    return auctions

@app.put("/auctions/{auction_id}", response_model=AuctionSchema)
def update_auction(auction_id: int, payload: AuctionSchema, db: Session = Depends(get_db)):
    auction = db.query(AuctionModel).filter(AuctionModel.auction_id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Update auction attributes
    for key, value in payload.dict().items():
        setattr(auction, key, value)
    
    db.commit()
    db.refresh(auction)
    return auction

@app.delete("/auctions/{auction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_auction(auction_id: int, db: Session = Depends(get_db)):
    auction = db.query(AuctionModel).filter(AuctionModel.auction_id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    auction.status = AuctionStatus.Cancelled
    db.commit()
    return


@app.put("/auctions/{auction_id}/start", response_model=AuctionSchema)
def start_auction(auction_id: int, db: Session = Depends(get_db)):
    auction = db.query(AuctionModel).filter(AuctionModel.auction_id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    auction.status = AuctionStatus.Active
    auction.start_time = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    
    # Notify relevant services about auction start
    try:
        requests.post(f"http://notifications-service:8000/notifications/auction/{auction_id}/started")
    except:
        # Log error but continue
        pass
    
    return auction

@app.put("/auctions/{auction_id}/end", response_model=AuctionSchema)
def end_auction(auction_id: int, db: Session = Depends(get_db)):
    auction = db.query(AuctionModel).filter(AuctionModel.auction_id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    auction.status = AuctionStatus.Closed
    db.commit()
    db.refresh(auction)
    
    # Process auction end (notify winner, etc.)
    try:
        process_auction(auction_id)
    except Exception as e:
        # Log error but continue
        pass
    
    return auction

@app.get("/auctions/{auction_id}/bids")
def get_auction_bids(auction_id: int):
    try:
        response = requests.get(f"http://bidding-service:8000/bids/auction/{auction_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching bids")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with bidding service: {str(e)}")

@app.get("/auctions/user/{user_id}", response_model=List[AuctionSchema])
def get_user_auctions(user_id: int, db: Session = Depends(get_db)):
    # In this implementation, we assume the auction service knows about auction creators
    # In a real implementation, you might need to check with items service or user service
    try:
        # Get user items first
        response = requests.get(f"http://items-service:8000/items/user/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching user items")
        
        user_item_ids = [item["item_id"] for item in response.json()]
        auctions = db.query(AuctionModel).filter(AuctionModel.item_id.in_(user_item_ids)).all()
        return auctions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.put("/auctions/{auction_id}/current_price", response_model=AuctionSchema)
def update_current_price(auction_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    auction = db.query(AuctionModel).filter(AuctionModel.auction_id == auction_id).first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if "current_price" not in data:
        raise HTTPException(status_code=400, detail="Missing 'current_price' in request body")
    auction.current_price = data["current_price"]
    db.commit()
    db.refresh(auction)
    return auction
