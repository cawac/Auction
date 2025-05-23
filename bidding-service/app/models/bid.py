# Bid model for bidding-service 
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Bid(Base):
    __tablename__ = 'bid'
    bid_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    auction_id = Column(Integer, nullable=False)
    bidder_id = Column(Integer, nullable=False)
    bid_amount = Column(Float, nullable=False)
    bid_time = Column(DateTime, default=datetime.datetime.utcnow)