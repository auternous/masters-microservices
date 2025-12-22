from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WorkoutCreate(BaseModel):
    name: str
    reps: int
    difficulty: int  # 1-5
    description: Optional[str] = None
    user_id: str 

class WorkoutUpdate(BaseModel):
    name: Optional[str] = None
    reps: Optional[int] = None
    difficulty: Optional[int] = None
    description: Optional[str] = None
    user_id: Optional[str] = None

class Workout(WorkoutCreate):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
