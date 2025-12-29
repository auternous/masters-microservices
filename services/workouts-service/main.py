import asyncio
import os
import time
from contextlib import asynccontextmanager

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

from models import WorkoutCreate, WorkoutUpdate
from database import connect_to_mongo, close_mongo, create_workout, get_workout, get_all_workouts, update_workout, delete_workout, get_workouts_collection
from kafka_handler import workout_kafka

load_dotenv()
consumer_task = None

# Отдельный реестр метрик для этого сервиса
REGISTRY = CollectorRegistry()

# Prometheus метрики
REQUEST_TIME = Histogram(
    'workouts_http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)
REQUEST_COUNT = Counter(
    'workouts_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)
WORKOUTS_CREATED = Counter('workouts_created_total', 'Total workouts created', registry=REGISTRY)
WORKOUTS_UPDATED = Counter('workouts_updated_total', 'Total workouts updated', registry=REGISTRY)
WORKOUTS_DELETED = Counter('workouts_deleted_total', 'Total workouts deleted', registry=REGISTRY)
WORKOUTS_ASSIGNED = Counter('workouts_assigned_total', 'Total workouts assigned to users', registry=REGISTRY)

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

# Prometheus endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type="text/plain; version=0.0.4")

# Middleware для метрик
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    # Пропускаем сам /metrics endpoint чтобы не было рекурсии
    if request.url.path == "/metrics":
        return await call_next(request)
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_TIME.labels(method=request.method, endpoint=request.url.path).observe(process_time)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

@app.post("/workouts", response_model=dict, tags=["Workouts"])
async def create_new_workout(workout: WorkoutCreate):
    workout_dict = workout.model_dump()
    workout_id = await create_workout(workout_dict)
    WORKOUTS_CREATED.inc()
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
    WORKOUTS_UPDATED.inc()
    await workout_kafka.send_event("workout.updated", {"id": workout_id})
    return {"status": "updated"}

@app.delete("/workouts/{workout_id}", tags=["Workouts"])
async def delete_one_workout(workout_id: str):
    if not ObjectId.is_valid(workout_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    success = await delete_workout(workout_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    WORKOUTS_DELETED.inc()
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
    WORKOUTS_ASSIGNED.inc()
    await workout_kafka.send_event("workout.assigned", {"workout_id": workout_id, "user_id": user_id})
    return {"status": "assigned"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "workouts"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)
