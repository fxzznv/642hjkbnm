import os

from kafka import KafkaConsumer
from dotenv import  load_dotenv

load_dotenv()

def create_consumer():
    kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    print(kafka_broker)
    return KafkaConsumer(
        'valids',
        bootstrap_servers=kafka_broker,
        group_id='my-pidoras-group',
        auto_offset_reset='latest',  # Важно: что делать при отсутствии коммитов
        value_deserializer=lambda m: m.decode('utf-8'),  # Для JSON данных
        enable_auto_commit=False,
    )