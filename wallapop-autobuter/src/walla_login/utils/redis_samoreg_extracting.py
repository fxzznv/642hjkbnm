import os
import redis

from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    password=REDIS_PASSWORD
)

def extract_samoreg():
    try:
        _, samoreg = redis_client.brpop("samoregi:list", timeout=0)
        print("Получен саморег:", samoreg)
        try:
            samoreg_mail, samoreg_pass = samoreg.split(":", 1)
            if not samoreg_mail or not samoreg_pass:
                raise ValueError("Неверный формат саморега: email или пароль пусты")
            return samoreg_mail, samoreg_pass
        except ValueError as e:
            print(f"Ошибка разбора саморега '{samoreg}': {e}")
            raise
    except redis.RedisError as re:
        print(f"Ошибка Redis при извлечении саморега: {re}")
        raise

def push_samoreg_back(mail: str, password: str):
    samoreg = f"{mail}:{password}"
    redis_client.rpush("samoregi:list", samoreg)
    print("Добавлен саморег:", samoreg)

if __name__ == "__main__":
    print(f"REDIS_HOST: {REDIS_HOST}:{type(REDIS_HOST)}\n"
          f"REDIS_HOST: {REDIS_PORT}:{type(REDIS_PORT)}\n"
          f"REDIS_HOST: {REDIS_PASSWORD}:{type(REDIS_PASSWORD)}\n")