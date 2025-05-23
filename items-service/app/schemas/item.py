# Item schema for items-service 
from pydantic import BaseModel
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    
class ItemCreate(ItemBase):
    """Schema for creating new items."""
    pass

class Item(ItemBase):
    """Schema for returning items."""
    item_id: int

    class Config:
        from_attributes = True 