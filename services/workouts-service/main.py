import asyncio
import os
from contextlib import asynccontextmanager
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from models import WorkoutCreate, WorkoutUpdate
from database import connect_to_mongo, close_mongo, create_workout, get_workout, get_all_workouts, update_workout, delete_workout
from kafka_handler import workout_kafka

load_dotenv()
consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    await connect_to_mongo()
    consumer_task = asyncio.create_task(workout_kafka.start_consumer())
    print("✓ Workouts Service STARTED\n")
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    await close_mongo()
    workout_kafka.close()
    print("✓ Workouts Service STOPPED")

app = FastAPI(title="Workouts Service", version="1.0.0", description="Workout Management", lifespan=lifespan)

@app.post("/workouts", response_model=dict, tags=["Workouts"])
async def create_new_workout(workout: WorkoutCreate):
    workout_dict = workout.model_dump()
    workout_id = await create_workout(workout_dict)
    await workout_kafka.send_event("workout.created", {"id": workout_id, "name": workout.name, "user_id": workout.user_id})
    return {"id": workout_id, "status": "created"}

@app.get("/workouts/{workout_id}", tags=["Workouts"])
async def get_one_workout(workout_id: str):
    if not ObjectId.is_valid(workout_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    workout = await get_workout(workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Not found")
    workout["_id"] = str(workout["_id"])
    return workout

@app.get("/workouts", tags=["Workouts"])
async def list_workouts(skip: int = 0, limit: int = 10):
    workouts = await get_all_workouts(skip, limit)
    for w in workouts:
        w["_id"] = str(w["_id"])
    return workouts

@app.get("/users/{user_id}/workouts", tags=["Workouts"])
async def get_user_workouts_list(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    collection = await get_workouts_collection()
    workouts = await collection.find({"user_id": user_id}).to_list(length=None)
    for w in workouts:
        w["_id"] = str(w["_id"])
    return workouts

@app.put("/workouts/{workout_id}", tags=["Workouts"])
async def update_one_workout(workout_id: str, workout: WorkoutUpdate):
    if not ObjectId.is_valid(workout_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    update_data = {k: v for k, v in workout.model_dump().items() if v is not None}
    if not update_:
        raise HTTPException(status_code=400, detail="No data to update")
    success = await update_workout(workout_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    await workout_kafka.send_event("workout.updated", {"id": workout_id})
    return {"status": "updated"}

@app.delete("/workouts/{workout_id}", tags=["Workouts"])
async def delete_one_workout(workout_id: str):
    if not ObjectId.is_valid(workout_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    success = await delete_workout(workout_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    await workout_kafka.send_event("workout.deleted", {"id": workout_id})
    return {"status": "deleted"}

@app.post("/workouts/{workout_id}/assign/{user_id}", tags=["Workouts"])
async def assign_workout(workout_id: str, user_id: str):
    if not ObjectId.is_valid(workout_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    workout = await get_workout(workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    success = await update_workout(workout_id, {"user_id": user_id})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to assign workout")
    await workout_kafka.send_event("workout.assigned", {"workout_id": workout_id, "user_id": user_id})
    return {"status": "assigned"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "workouts"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
