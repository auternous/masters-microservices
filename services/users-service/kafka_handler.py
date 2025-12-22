import asyncio
import json
import os
from kafka import KafkaProducer
import aiokafka

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

class UserKafkaHandler:
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
            future = self.producer.send("user_events", value=event)
            future.get(timeout=10)
            print(f"✓ SENT: {event_type}")
        except Exception as e:
            print(f"✗ SEND ERROR: {e}")

    async def start_consumer(self):
        """Запуск асинхронного consumer'а для workout_events"""
        try:
            self.consumer = aiokafka.AIOKafkaConsumer(
                "workout_events",
                bootstrap_servers=KAFKA_SERVERS,
                group_id="users-service",
                auto_offset_reset="earliest",
            )
            await self.consumer.start()
            print("👂 Consumer STARTED (listening workout_events)\n")

            try:
                async for message in self.consumer:
                    event = json.loads(message.value.decode("utf-8"))
                    event_type = event.get("type")
                    event_data = event.get("data", {})

                    print(f"📨 RECEIVED: {event_type}")

                    if event_type == "workout.created":
                        print(f"   💪 Workout '{event_data.get('name')}' created\n")
                    elif event_type == "workout.updated":
                        print(f"   🔄 Workout updated\n")
                    elif event_type == "workout.deleted":
                        print(f"   🗑️ Workout deleted\n")

            except asyncio.CancelledError:
                print("Consumer stopped")
        except Exception as e:
            print(f"✗ CONSUMER ERROR: {e}")
        finally:
            if self.consumer:
                await self.consumer.stop()

    def close(self):
        self.producer.close()

user_kafka = UserKafkaHandler()
