# Workout Microservices System

## Структура проекта

```
workout-system/
├── docker-compose.yml
├── requirements.txt
├── .env
├── README.md
├── services/
│   ├── workouts-service/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── kafka_producer.py
│   │   └── requirements.txt
│   │
│   └── users-service/
│       ├── main.py
│       ├── models.py
│       ├── database.py
│       ├── kafka_producer.py
│       └── requirements.txt
```

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск инфраструктуры (MongoDB + Kafka)

```bash
docker-compose up -d
```

### 3. Запуск микросервисов

В отдельных терминалах:

```bash
# Терминал 1: Workouts Service
cd services/workouts-service
python main.py
```

```bash
# Терминал 2: Users Service
cd services/users-service
python main.py
```

Сервисы будут доступны:
- Workouts Service: http://localhost:8001
- Users Service: http://localhost:8002

## API Endpoints

### Workouts Service

- `POST /workouts` - Создание тренировки
- `GET /workouts` - Список всех тренировок
- `GET /workouts/{workout_id}` - Получение тренировки по ID
- `PUT /workouts/{workout_id}` - Обновление тренировки
- `DELETE /workouts/{workout_id}` - Удаление тренировки
- `GET /health` - Проверка здоровья сервиса

### Users Service

- `POST /users` - Создание пользователя
- `GET /users` - Список всех пользователей
- `GET /users/{user_id}` - Получение пользователя по ID
- `PUT /users/{user_id}` - Обновление пользователя
- `DELETE /users/{user_id}` - Удаление пользователя
- `GET /health` - Проверка здоровья сервиса

## Примеры использования

### Создание тренировки

```bash
curl -X POST "http://localhost:8001/workouts" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pushups",
    "reps": 20,
    "difficulty": 3,
    "description": "Standard pushups"
  }'
```

### Получение всех тренировок

```bash
curl "http://localhost:8001/workouts"
```

### Обновление тренировки

```bash
curl -X PUT "http://localhost:8001/workouts/{workout_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "reps": 25,
    "difficulty": 4
  }'
```

## Порты

- MongoDB: 27017
- Kafka: 9092
- Zookeeper: 2181
- Workouts Service: 8001
- Users Service: 8002

## Остановка сервисов

```bash
# Остановка Docker контейнеров
docker-compose down
```

## Troubleshooting

### Docker daemon не запущен

Если видишь ошибку "Cannot connect to the Docker daemon", нужно запустить Docker Desktop.

### ImportError в motor

Если ошибка типа "cannot import name 'AsyncClient'", убедись что используешь `AsyncIOMotorClient` вместо `AsyncClient`.

Это уже исправлено в актуальных файлах.
