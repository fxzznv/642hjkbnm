import redis
import docker
import time
import os

# Конфигурация
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
SERVICE_3_NAME = 'captcha-service'
DELAY = 40  # Задержка перед остановкой
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    password=REDIS_PASSWORD
)

docker_client = docker.from_env()

def check_heartbeats():
    """Проверяет наличие активных сердцебиений"""
    keys = redis_client.keys('worker_heartbeat:*')
    return len(keys) > 0


def manage_service3(should_run):
    """Управляет состоянием Сервиса №3"""
    try:
        containers = docker_client.containers.list(
            filters={'name': SERVICE_3_NAME}
        )

        if should_run and not containers:
            print("Запуск Сервиса №3")
            # Запуск через docker-compose
            os.system(f"docker-compose up -d {SERVICE_3_NAME}")
        elif not should_run and containers:
            print("Остановка Сервиса №3")
            os.system(f"docker-compose stop {SERVICE_3_NAME}")
    except Exception as e:
        print(f"Ошибка управления контейнером: {e}")


# Основной цикл монитора
last_active = False
inactive_since = None

while True:
    has_heartbeats = check_heartbeats()

    if has_heartbeats and not last_active:
        # Первое обнаружение активности
        manage_service3(True)
        last_active = True
        inactive_since = None

    elif not has_heartbeats and last_active:
        # Активность прекратилась
        if inactive_since is None:
            inactive_since = time.time()
        elif time.time() - inactive_since > DELAY:
            manage_service3(False)
            last_active = False
            inactive_since = None

    time.sleep(5)