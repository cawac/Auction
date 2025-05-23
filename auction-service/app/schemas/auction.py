from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class AuctionStatus(str, Enum):
    Active = "Active"
    Closed = "Closed"
    Cancelled = "Cancelled"


class AuctionCreate(BaseModel):
    item_id: int
    start_time: datetime
    end_date: datetime
    starting_price: float
    current_price: float
    status: AuctionStatus
    class Config:
        from_attributes = True 

class Auction(AuctionCreate):
    auction_id: int
    class Config:
        from_attributes = True
