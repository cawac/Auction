from fastapi import FastAPI, Depends, HTTPException, status
from .models.item import Item, Base
from .schemas.item import Item as ItemSchema, ItemCreate
from sqlalchemy.orm import Session
from .sqlalchemy_conn import engine, get_db
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wait for database to be ready
time.sleep(5)

# Explicitly drop and recreate tables on startup
logger.info("Creating database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

app = FastAPI()

# CRUD Operations
@app.post("/items", response_model=ItemSchema, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = Item(
        name=item.name,
        description=item.description,
        category_id=item.category_id
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.get("/items/{item_id}", response_model=ItemSchema)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/items", response_model=list[ItemSchema])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

@app.put("/items/{item_id}", response_model=ItemSchema)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.item_id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update allowed fields
    update_data = item.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return None

# Items by category
@app.get("/items/category/{category_id}", response_model=list[ItemSchema])
def get_category_items(category_id: int, db: Session = Depends(get_db)):
    return db.query(Item).filter(Item.category_id == category_id).all()