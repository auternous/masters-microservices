from pymongo import MongoClient
from kafka import KafkaProducer, KafkaConsumer
import os
import time

# MongoDB
mongo_url = os.getenv("MONGO_URL", "mongodb://root:password@localhost:27017")
mongo_client = MongoClient(mongo_url)

try:
    mongo_client.admin.command('ping')
    print("✓ MongoDB connected")
except Exception as e:
    print(f"✗ MongoDB error: {e}")

# Kafka
kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(',')

try:
    # Важно: client_id и request_timeout_ms
    producer = KafkaProducer(
        bootstrap_servers=kafka_servers,
        client_id='test-producer',
        request_timeout_ms=10000,
        retries=3
    )
    
    # Отправи тестовое сообщение
    future = producer.send('test-topic', b'Hello Kafka')
    record_metadata = future.get(timeout=10)
    
    producer.close()
    print("✓ Kafka connected")
except Exception as e:
    print(f"✗ Kafka error: {e}")
    import traceback
    traceback.print_exc()
