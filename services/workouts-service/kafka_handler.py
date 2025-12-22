import asyncio
import json
import os
from kafka import KafkaProducer
import aiokafka

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

class WorkoutKafkaHandler:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=3,
            api_version=(2, 8, 0),
        )
        self.consumer = None

    async def send_event(self, event_type: str,  dict):
        """Отправка события в Kafka"""
        try:
            event = {"type": event_type, "data": data}
            future = self.producer.send("workout_events", value=event)
            future.get(timeout=10)
            print(f"✓ SENT: {event_type}")
        except Exception as e:
            print(f"✗ SEND ERROR: {e}")

    async def start_consumer(self):
        """Запуск асинхронного consumer'а для user_events"""
        try:
            self.consumer = aiokafka.AIOKafkaConsumer(
                "user_events",
                bootstrap_servers=KAFKA_SERVERS,
                group_id="workouts-service",
                auto_offset_reset="earliest",
            )
            await self.consumer.start()
            print("👂 Consumer STARTED (listening user_events)\n")

            try:
                async for message in self.consumer:
                    event = json.loads(message.value.decode("utf-8"))
                    event_type = event.get("type")
                    event_data = event.get("data", {})

                    print(f"📨 RECEIVED: {event_type}")

                    if event_type == "user.created":
                        print(f"   ➕ User '{event_data.get('username')}' created\n")
                    elif event_type == "user.updated":
                        print(f"   🔄 User updated\n")
                    elif event_type == "user.deleted":
                        print(f"   🗑️ User deleted\n")

            except asyncio.CancelledError:
                print("Consumer stopped")
        except Exception as e:
            print(f"✗ CONSUMER ERROR: {e}")
        finally:
            if self.consumer:
                await self.consumer.stop()

    def close(self):
        self.producer.close()

workout_kafka = WorkoutKafkaHandler()
