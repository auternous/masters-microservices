import strawberry
from typing import List, Optional, Any

@strawberry.type
class User:
    id: strawberry.ID
    username: str
    email: str

@strawberry.type
class Workout:
    id: strawberry.ID
    name: str
    reps: int
    difficulty: int
    user_id: Optional[str] = None

@strawberry.input
class CreateUserInput:
    username: str
    email: str

@strawberry.input
class CreateWorkoutInput:
    name: str
    reps: int
    difficulty: int
    user_id: str

# Гибкие функции для MongoDB данных
def mongo_to_user(mongo_user: dict) -> User:
    """Преобразует MongoDB документ в User (игнорирует лишние поля)"""
    # Берем только нужные поля
    user_data = {
        "id": str(mongo_user.get("_id", "")),
        "username": mongo_user.get("username", ""),
        "email": mongo_user.get("email", "")
    }
    return User(**user_data)

def mongo_to_workouts(mongo_workouts: list) -> List[Workout]:
    """Преобразует список MongoDB документов в Workout"""
    workouts = []
    for w in mongo_workouts:
        workout_data = {
            "id": str(w.get("_id", "")),
            "name": w.get("name", ""),
            "reps": w.get("reps", 0),
            "difficulty": w.get("difficulty", 0),
            "user_id": w.get("user_id")
        }
        workouts.append(Workout(**workout_data))
    return workouts
