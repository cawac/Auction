from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr

class UserOut(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr

    class Config:
        orm_mode = True
