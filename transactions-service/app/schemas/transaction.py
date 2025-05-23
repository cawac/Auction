# Transaction schema for transactions-service 
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"


class TransactionBase(BaseModel):
    auction_id: int
    buyer_id: int
    transaction_date: datetime
    status: TransactionStatus
    class Config:
        from_attributes = True 


class TransactionCreate(TransactionBase):
    class Config:
        from_attributes = True

class TransactionSchema(TransactionBase):
    transaction_id: int
    class Config:
        from_attributes = True