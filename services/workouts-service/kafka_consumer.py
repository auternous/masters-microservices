import asyncio
import aiokafka
import json
import os
from database import get_workouts_collection

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

async def user_events_consumer():
    """Асинхронный consumer событий пользователей"""
    try:
        consumer = aiokafka.AIOKafkaConsumer(
            'user_events',
            bootstrap_servers=KAFKA_SERVERS,
            group_id='workouts-user-group'
        )
        await consumer.start()
        print("👂 Workouts Consumer: слушаю user_events...")
        
        async for msg in consumer:
            event = json.loads(msg.value.decode('utf-8'))
            print(f"📨 Получено событие: {event['type']}")
            
            if event['type'] == 'user.created':
                user_id = event['data']['id']
                print(f"➕ Новый пользователь {user_id}")
                
    except Exception as e:
        print(f"✗ Consumer error: {e}")
    finally:
        await consumer.stop()
