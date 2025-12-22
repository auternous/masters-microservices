import asyncio
import os
from contextlib import asynccontextmanager
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from models import UserCreate, UserUpdate
from database import connect_to_mongo, close_mongo, create_user, get_user, get_all_users, update_user, delete_user, get_users_collection
from kafka_handler import user_kafka

load_dotenv()
consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    await connect_to_mongo()
    consumer_task = asyncio.create_task(user_kafka.start_consumer())
    print("✓ Users Service STARTED\n")
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    await close_mongo()
    user_kafka.close()
    print("✓ Users Service STOPPED")

app = FastAPI(title="Users Service", version="1.0.0", description="User Management", lifespan=lifespan)

@app.post("/users", response_model=dict, tags=["Users"])
async def create_new_user(user: UserCreate):
    user_dict = user.model_dump()
    user_id = await create_user(user_dict)
    await user_kafka.send_event("user.created", {"id": user_id, "username": user.username, "email": user.email})
    return {"id": user_id, "status": "created"}

@app.get("/users/{user_id}", tags=["Users"])
async def get_one_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    user["_id"] = str(user["_id"])
    return user

@app.get("/users", tags=["Users"])
async def list_users(skip: int = 0, limit: int = 10):
    users = await get_all_users(skip, limit)
    for u in users:
        u["_id"] = str(u["_id"])
    return users

@app.put("/users/{user_id}", tags=["Users"])
async def update_one_user(user_id: str, user: UserUpdate):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    update_data = {k: v for k, v in user.model_dump().items() if v is not None}
    if not update_:
        raise HTTPException(status_code=400, detail="No data to update")
    success = await update_user(user_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    await user_kafka.send_event("user.updated", {"id": user_id, "fields": list(update_data.keys())})
    return {"status": "updated"}

@app.delete("/users/{user_id}", tags=["Users"])
async def delete_one_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    await user_kafka.send_event("user.deleted", {"id": user_id})
    return {"status": "deleted"}

@app.get("/users/{user_id}/workouts", tags=["Users"])
async def get_user_assigned_workouts(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Получаем workouts из workout_db.workouts
    from database import db
    workouts = await db.db["workouts"].find({"user_id": user_id}).to_list(length=None)
    for w in workouts:
        w["_id"] = str(w["_id"])
    return workouts

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "users"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
