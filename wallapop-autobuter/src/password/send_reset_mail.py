from src.logging.logger_init import setup_logger

logger = setup_logger(__name__)


def send_reset_email(session, email):
    reset_url = "https://api.wallapop.com/shnm-portlet/api/v1/access.json/passwordRecovery"
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip, deflate, br, zstd",
        "Accept-language": "be,en-US;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://es.wallapop.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    logger.info("Начало send_reset_email:")
    payload = {"emailaddress": email}

    for attempt in range(3):

        try:
            response = session.post(reset_url, headers=headers, data=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"(send_reset_email): {email} -> Статус: {response.status_code}")
                print(f"[+] {email} -> Статус: {response.status_code}")
                return True
            else:
                logger.warning(f"(send_reset_email): {email} -> Попытка {attempt+1}, код: {response.status_code}")
                print(f"[!] {email} -> Попытка {attempt+1}, код: {response.status_code}")
        except Exception as e:
            logger.error(f"(send_reset_email): Ошибка для {email} на попытке {attempt+1}: {e}")
            print(f"[!] Ошибка для {email} на попытке {attempt+1}: {e}")
            return False
    logger.error(f"(send_reset_emai): {email}. 3 попытки дали отрицательный ответ. Возможно, стоит проверить работоспособность API")
    print(f"(send_reset_emai): {email}. 3 попытки дали отрицательный ответ. Возможно, стоит проверить работоспособность API")
    return False
