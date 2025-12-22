from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from datetime import datetime
from bson import ObjectId

MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:password@localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "workout_db")

class Database:
    client: 'AsyncIOMotorClient'  = None
    db: 'AsyncIOMotorDatabase' = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGO_URL)
    db.db = db.client[MONGO_DB]
    # Создаём индексы для быстрого поиска
    await db.db["users"].create_index("email", unique=True)
    await db.db["users"].create_index("username", unique=False)
    print("✓ Connected to MongoDB")

async def close_mongo():
    if db.client:
        db.client.close()
        print("✓ Closed MongoDB connection")

async def get_users_collection():
    return db.db["users"]

# CRUD операции
async def create_user(user_data: dict):
    collection = await get_users_collection()
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    result = await collection.insert_one(user_data)
    return str(result.inserted_id)

async def get_user(user_id: str):
    collection = await get_users_collection()
    return await collection.find_one({"_id": ObjectId(user_id)})

async def get_all_users(skip: int = 0, limit: int = 10):
    collection = await get_users_collection()
    cursor = collection.find({}).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return users

async def update_user(user_id: str, update_data: dict):
    collection = await get_users_collection()
    update_data["updated_at"] = datetime.utcnow()
    result = await collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_user(user_id: str):
    collection = await get_users_collection()
    result = await collection.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0
