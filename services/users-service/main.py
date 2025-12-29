import asyncio
import os
import time
from contextlib import asynccontextmanager

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

from models import UserCreate, UserUpdate
from database import connect_to_mongo, close_mongo, create_user, get_user, get_all_users, update_user, delete_user
from kafka_handler import user_kafka

load_dotenv()
consumer_task = None

# Отдельный реестр метрик для этого сервиса
REGISTRY = CollectorRegistry()

# Prometheus метрики
REQUEST_TIME = Histogram(
    'users_http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)
REQUEST_COUNT = Counter(
    'users_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)
USERS_CREATED = Counter('users_created_total', 'Total users created', registry=REGISTRY)
USERS_UPDATED = Counter('users_updated_total', 'Total users updated', registry=REGISTRY)
USERS_DELETED = Counter('users_deleted_total', 'Total users deleted', registry=REGISTRY)

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

@app.post("/users", response_model=dict, tags=["Users"])
async def create_new_user(user: UserCreate):
    user_dict = user.model_dump()
    user_id = await create_user(user_dict)
    USERS_CREATED.inc()
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
    if not update_ :
        raise HTTPException(status_code=400, detail="No data to update")
    success = await update_user(user_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    USERS_UPDATED.inc()
    await user_kafka.send_event("user.updated", {"id": user_id, "fields": list(update_data.keys())})
    return {"status": "updated"}

@app.delete("/users/{user_id}", tags=["Users"])
async def delete_one_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    USERS_DELETED.inc()
    await user_kafka.send_event("user.deleted", {"id": user_id})
    return {"status": "deleted"}

@app.get("/users/{user_id}/workouts", tags=["Users"])
async def get_user_assigned_workouts(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
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
