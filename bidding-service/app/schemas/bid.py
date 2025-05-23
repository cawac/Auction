# Bid schema for bidding-service 
from pydantic import BaseModel
from datetime import datetime

class BidCreate(BaseModel):
    auction_id: int
    bidder_id: int
    bid_amount: float
    bid_time: datetime

    class Config:
        from_attributes = True 

class Bid(BidCreate):
    bid_id: int
    class Config:
        from_attributes = True 