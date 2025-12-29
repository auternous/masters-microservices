import strawberry
import httpx
from typing import List, Optional
from models import User, Workout, CreateUserInput, CreateWorkoutInput, mongo_to_user, mongo_to_workouts

@strawberry.type
class Query:
    @strawberry.field
    async def users(self) -> List[User]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8002/users")
            data = resp.json()
            return [mongo_to_user(user) for user in data]
    
    @strawberry.field
    async def user(self, id: str) -> Optional[User]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://localhost:8002/users/{id}")
            if resp.status_code == 200:
                return mongo_to_user(resp.json())
            return None
    
    @strawberry.field
    async def workouts(self) -> List[Workout]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8001/workouts")
            data = resp.json()
            return mongo_to_workouts(data)
    
    @strawberry.field
    async def user_workouts(self, user_id: str) -> List[Workout]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://localhost:8001/users/{user_id}/workouts")
            return mongo_to_workouts(resp.json())

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_user(self, input: CreateUserInput) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:8002/users", 
                                   json={"username": input.username, "email": input.email})
            return resp.json()["id"]
    
    @strawberry.mutation
    async def create_workout(self, input: CreateWorkoutInput) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:8001/workouts",
                                   json={"name": input.name, 
                                         "reps": input.reps, 
                                         "difficulty": input.difficulty,
                                         "user_id": input.user_id})
            return resp.json()["id"]

schema = strawberry.Schema(query=Query, mutation=Mutation)
