from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from datetime import datetime
from bson import ObjectId

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:password@localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "workout_db")

class Database:
    client: 'AsyncIOMotorClient' = None
    db: 'AsyncIOMotorDatabase'  = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGO_URL)
    db.db = db.client[MONGO_DB]
    # Создаём индекс для быстрого поиска
    await db.db["workouts"].create_index("name", unique=False)
    print("✓ Connected to MongoDB")

async def close_mongo():
    if db.client:
        db.client.close()
        print("✓ Closed MongoDB connection")

async def get_workouts_collection():
    return db.db["workouts"]

# CRUD операции
async def create_workout(workout_data: dict):
    collection = await get_workouts_collection()
    workout_data["created_at"] = datetime.utcnow()
    workout_data["updated_at"] = datetime.utcnow()
    result = await collection.insert_one(workout_data)
    return str(result.inserted_id)

async def get_workout(workout_id: str):
    collection = await get_workouts_collection()
    return await collection.find_one({"_id": ObjectId(workout_id)})

async def get_all_workouts(skip: int = 0, limit: int = 10):
    collection = await get_workouts_collection()
    cursor = collection.find({}).skip(skip).limit(limit)
    workouts = await cursor.to_list(length=limit)
    return workouts

async def update_workout(workout_id: str, update_data: dict):
    collection = await get_workouts_collection()
    update_data["updated_at"] = datetime.utcnow()
    result = await collection.update_one(
        {"_id": ObjectId(workout_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_workout(workout_id: str):
    collection = await get_workouts_collection()
    result = await collection.delete_one({"_id": ObjectId(workout_id)})
    return result.deleted_count > 0
