from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    age: Optional[int] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None

class User(UserCreate):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
