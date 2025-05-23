from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
import datetime

Base = declarative_base()

class AuctionStatus(str, PyEnum):
    Active = "Active"
    Closed = "Closed"
    Cancelled = "Cancelled"

class Auction(Base):
    __tablename__ = 'auctions'

    auction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    starting_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    status = Column(Enum(AuctionStatus), nullable=False)