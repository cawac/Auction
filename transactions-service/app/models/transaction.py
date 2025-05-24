# Transaction model for transactions-service 
from sqlalchemy import Column, Integer, Float, DateTime, Enum, String
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
import datetime
from sqlalchemy.sql import func

Base = declarative_base()

class TransactionStatus(str, PyEnum):
    Pending = "Pending"
    Completed = "Completed"
    Failed = "Failed"

class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    auction_id = Column(Integer, nullable=False)
    buyer_id = Column(Integer, nullable=False)
    transaction_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    status = Column(Enum(TransactionStatus), nullable=False)
    amount = Column(Float, nullable=False)