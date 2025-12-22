import asyncio
import aiokafka
import json
import os
from database import get_users_collection

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

async def workout_events_consumer():
    """Асинхронный consumer событий тренировок"""
    try:
        consumer = aiokafka.AIOKafkaConsumer(
            'workout_events',
            bootstrap_servers=KAFKA_SERVERS,
            group_id='users-workout-group'
        )
        await consumer.start()
        print("👂 Users Consumer: слушаю workout_events...")
        
        async for msg in consumer:
            event = json.loads(msg.value.decode('utf-8'))
            print(f"📨 Получено событие: {event['type']}")
            
            if event['type'] == 'workout.created':
                workout_name = event['data']['name']
                print(f"💪 Новая тренировка '{workout_name}'")
                
    except Exception as e:
        print(f"✗ Consumer error: {e}")
    finally:
        await consumer.stop()
