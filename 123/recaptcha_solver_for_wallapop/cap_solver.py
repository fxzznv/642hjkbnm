import os
import sys
import redis
from concurrent.futures.thread import ThreadPoolExecutor
import time

from redis import ConnectionPool
from twocaptcha import TwoCaptcha
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
API_2CAPTCHA = os.getenv('API_2CAPTCHA')
SITEKEY = os.getenv('SITEKEY')
PAGE_URL = os.getenv('PAGE_URL')

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS'))

NUM_THREADS = int(os.getenv('CAPTCHA_NUM_THREADS'))

api_key = os.getenv('APIKEY_2CAPTCHA', API_2CAPTCHA)
# print(API_2CAPTCHA, api_key)
solver = TwoCaptcha(api_key)


class RedisManager:
    _pool = None

    @classmethod
    def get_redis(cls):
        if cls._pool is None:
            cls._pool = ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                max_connections=REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return redis.Redis(connection_pool=cls._pool)

def solve_wallapop_captcha():
    redis_client = RedisManager.get_redis()
    try:
        result = solver.recaptcha(
            sitekey=SITEKEY,
            url=PAGE_URL,
            enterprise=1,
            version='v2'
        )

    except Exception as e:
        # sys.exit(e)
        print("captcha unsolvable")

    else:
        # print('solved: ' + str(result))
        code = extract_code_from_result(result)
        # print("Token:", code)

        redis_client.rpush("reCaptchaTTLToken:tokens", code)
        redis_client.expire("reCaptchaTTLToken:tokens", 60)

        print(code)
        return code

def extract_code_from_result(result: dict) -> str:
    return result.get("code")

def main(NUM_THREADS: int, pizda: str) -> None:
    if pizda == True:
        print(f"Запуск {NUM_THREADS} потоков для решения капч.")
        try:

            with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
                futures = [executor.submit(solve_wallapop_captcha) for _ in range(NUM_THREADS)]

                for future in futures:
                    try:
                        result = future.result()
                        if result:
                            print("Капча решена и записана в Redis")
                        else:
                            print("Не удалось решить капчу в одном из потоков")
                    except Exception as e:
                        print(f"Exception: {e}")
            print("Все потоки решения капч завершены.")

            redis_client = RedisManager.get_redis()
            tokens = redis_client.lrange("reCaptchaTTLToken:tokens", 0, -1)
            print(f"Токены, сохранённые в Redis: {tokens}")

        except Exception as e:
            print(f"Exception: {e}")

        finally:
            # можно закрыть пул, а можно хуй забить
            pass
    else:
        print("pizda = False")

def get_flag_from_redis():
    redis_client = RedisManager.get_redis()
    flag = redis_client.get("cap_solver_flag")
    return flag == "True"

if __name__ == '__main__':
    while True:
        flag = get_flag_from_redis()
        if flag:
            main(NUM_THREADS, True)
        else:
            print("Флаг выключен, ожидаем...")
            time.sleep(5)
        print("--------------------------------------------------------------------------------------------------------")

