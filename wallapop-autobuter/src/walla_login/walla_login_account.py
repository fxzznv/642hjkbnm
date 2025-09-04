from datetime import datetime
import random
import re
import time
import os
import redis
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from src.logging.logger_init import setup_logger
from src.mail.mail_api import generate_guid
from src.password.reset_password import get_last_email_token
from src.walla_login.utils.walla_login_constants import MPID, WALLA_BASE_DELAY, WALLA_MIN_DELAY, WALLA_DELAY_MULTIPLIER

logger = setup_logger(__name__)
load_dotenv()

device_id = generate_guid()
mpid = str(random.randint(-2**63, -1))
device_token = generate_guid()
counter = 0
DEV = device_id

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    password=REDIS_PASSWORD
)
def extract_redis_token():
    _, token = redis_client.brpop("reCaptchaTTLToken:tokens", timeout=0)
    print(f"{email} | {timestamp} | Получен токен: ", token)
    return token

def walla_go_login(session, email, password):
    session.get("https://es.wallapop.com")
    session.get("https://es.wallapop.com/auth/onboarding?redirectUrl=%2F")
    session.get("https://es.wallapop.com/auth/signin?redirectUrl=%2F")


    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
    cookie_string = "; ".join([f"{key}={value}" for key, value in cookies_dict.items()])


    print(f"{email} | {timestamp} | Ждем токен из редиса")
    token = extract_redis_token()
    url = "https://api.wallapop.com/api/v3/access/login"
    payload = {
        "emailAddress": email,
        "password": password,
        "metadata": {
            "recaptchaToken": token,
            "sessionId": generate_guid(),
            "profiling-status": "TMXStatusCodeOk",
        },
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "connection": "keep-alive",
        "content-type": "application/json",
        "origin": "https://es.wallapop.com",
        "referer": "https://es.wallapop.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "accept-language": "es,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6,be;q=0.5,tg;q=0.4",
        "deviceos": "0",
        "mpid": mpid,
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "x-appversion": "89210",
        "x-deviceid": DEV,
        "x-deviceos": "0",
        "x-devicetoken": DEV,
        "cookie": cookie_string,
    }

    try:
        response = session.post(url, headers=headers, json=payload)
        logger.info(f"(walla_go_login): {response.status_code}, {response.text}")
        print(f"(walla_go_login): {response.status_code}, {response.text}")

        if response.status_code == 403:
            data = response.json()
            channel = data.get("channel")
            if channel == "LOGIN":
                mfa_id = data.get("mfa_id")
                print(f"{channel}\n{mfa_id}")
                logger.debug(f"walla_go_login: Успех: {mfa_id}")
                return response.status_code, mfa_id, None
            else:
                logger.debug(f"walla_go_login: Ошибка телефона: {channel}")
                print("Требуется телефон")
                return None, None, None
        elif response.status_code == 200:
            print(f"{response.status_code}: {response.text}")
            data = response.json()
            token = data.get("token")
            reset_token = data.get("resetToken")
            return response.status_code, token, reset_token
        elif response.status_code == 400:
            return response.status_code, response.json(), None
        else:
            print(f"код {response.status_code}: {response.text}")
            print(response.status_code, response.text)
            return None, None, None

    except Exception as e:
        logger.error(f"walla_go_login: Exception: {e}")
        print(f"[!]Error: {e}")
        return None

def walla_validate(session, mfa_id: str, code: str):
    logger.info(f"(walla_validate): Вход")
    url = "https://api.wallapop.com/api/v3/mfa/validate"

    payload = {
        "mfa_id": mfa_id,
        "challenge_code": code
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "api.wallapop.com",
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "accept-language": "es,be;q=0.9,en-US;q=0.8",
        "deviceos": "0",
        "mpid": MPID,
        'sec-ch-ua': "Google Chrome",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "x-appversion": "87270",
        "x-deviceid": DEV,
        "x-deviceos": "0"
    }
    try:
        response = session.post(url, json=payload, headers=headers)
        logger.info(f"walla_validate: Запрос валидации: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"walla_validate: Exception: {e}")

def walla_authorize(session, mfa_id):
    logger.info(f"(walla_authorize): Вход")
    url = "https://api.wallapop.com/api/v3/access/authorize"

    payload = {
        "login-attempt-token": mfa_id
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "api.wallapop.com",
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "accept-language": "es,be;q=0.9,en-US;q=0.8",
        "deviceos": "0",
        "mpid": MPID,
        'sec-ch-ua': "Google Chrome",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "x-appversion": "87270",
        "x-deviceid": DEV,
        "x-deviceos": "0",
        "x-devicetoken": DEV,
    }


    try:
        response = session.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            reset_token = data.get("resetToken")
            print("Token:", token)
            logger.info(f"walla_authorize: Успех, токен auth: {token}")
            return token, reset_token
        else:
            print("Authorization failed:", response.status_code, response.text)
            logger.error("Authorization failed:", response.status_code, response.text)
            return None
    except Exception as e:
        logger.error(f"walla_authorize: Exception: {e}")
        print("Authorization failed:", e)
        return None

def get_email_verification_code(session, token: str, email_token, puid, canary):
    logger.info("Запуск get_email_verification_code")

    session.get("https://outlook.live.com/")
    url = "https://outlook.live.com/owa/0/service.svc?action=GetItem&app=Mail&n=26"

    headers = {
        "x-req-source": "Mail",
        "authorization": f'MSAuth1.0 usertoken="{token}", type="MSACT"',
        "action": "GetItem",
        "Referer": "",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-owa-hosted-ux": "false",
        "ms-cv": generate_guid(),
        "x-owa-sessionid": generate_guid(),
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "x-owa-actionsource": "PrefetchFirstN",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "content-type": "application/json; charset=utf-8",
        "x-owa-correlationid": generate_guid()
    }

    payload = {
        "__type": "GetItemJsonRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2017_08_18",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "SA Western Standard Time"
                }
            }
        },
        "Body": {
            "__type": "GetItemRequest:#Exchange",
            "ItemShape": {
                "__type": "ItemResponseShape:#Exchange",
                "BaseShape": "Default",
                "BodyShape": "UniqueFragment",
                "AdditionalProperties": [
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "Subject"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "Sender"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "ToRecipients"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "From"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "DateTimeReceived"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "UniqueBody"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "IsRead"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "HasAttachments"},
                    {"__type": "PropertyUri:#Exchange", "FieldURI": "Preview"}
                ],
                "FilterHtmlContent": True,
                "MaximumBodySize": 2097152
            },
            "ItemIds": [
                {
                    "__type": "ItemId:#Exchange",
                    "Id": email_token
                }
            ],
            "ShapeName": "ItemNormalizedBody"
        }
    }

    response_conversation = session.post(url, headers=headers, json=payload)
    if response_conversation.status_code != 200:
        logger.error(
            f"(get_email_verification_code): Status code {response_conversation.status_code}: {response_conversation.json()}")
        return None

    try:
        data_conversation = response_conversation.json()
        html_value = data_conversation["Body"]["ResponseMessages"]["Items"][0]["Items"][0]["Body"]["Value"]

        soup = BeautifulSoup(html_value, 'html.parser')
        # print("Полная HTML-разметка письма:")
        # print(soup.prettify())

        text_content = soup.get_text(strip=True)
        print(text_content)
        text_content = ' '.join(text_content.split())  # Нормализация пробелов
        match = re.search(r'\d{6}', text_content)

        if match:
            code = match.group(0)
            logger.info(f"Успех - код верификации: {code}")
            return code
        else:
            logger.error("(get_email_verification_code): Код верификации (6 цифр) не найден в тексте письма.")
            return None
    except (KeyError, IndexError) as e:
        logger.error(f"(get_email_verification_code): Ошибка доступа к UniqueBody: {e}")
        return None

def walla_login(session, email, password, mail_session, canary, token, queries,deleted_folderid, puid):
    try:
        max_attempts = 7
        base_delay = WALLA_BASE_DELAY
        min_delay = WALLA_MIN_DELAY
        delay_multiplier = WALLA_DELAY_MULTIPLIER

        current_delay = base_delay
        attempt = 1

        while attempt <= max_attempts:
            # time.sleep(current_delay)

            res = walla_go_login(session, email, password)
            status_code, result, reset_token = res
            if status_code == 200:
                return result, reset_token
            elif status_code == 403:
                mfa_id = result
                logger.info(f"MFA required for {email}, MFA ID: {mfa_id}")

                inner_attempt = 1
                inner_max_attempts = 5
                while inner_attempt <= inner_max_attempts:
                    email_id, sk = get_last_email_token(session=mail_session, canary=canary, token=token, puid=puid)
                    verification_code = get_email_verification_code(
                        session=mail_session,
                        puid=puid,
                        token=token,
                        email_token=email_id,
                        canary=canary)
                    if verification_code:
                        print(f"Verification code: {verification_code}\n На попытке {inner_attempt} - успех")
                        walla_validate(session, mfa_id, verification_code)
                        token, reset_token = walla_authorize(session, mfa_id)
                        return token, reset_token

                    print(f"Попытка получения кода письма: Попытка {inner_attempt}, Провал")
                    inner_attempt += 1
                    time.sleep(3)

                return None
            elif status_code == 400:
                print(f"Попытка {attempt} не удалась (статус 400). Следующая попытка через: {current_delay} сек")

                # Уменьшаем задержку для следующей попытки
                # current_delay = max(current_delay * delay_multiplier, min_delay)
                attempt += 1

                if attempt > max_attempts:
                    print("Достигнуто максимальное количество попыток (5).")
                    return None
            else:
                print(f"Неожиданный статус код: {status_code}")
                return None
        return None

    except Exception as e:
        print("walla_login failed:", e)
        return None

if __name__ == "__main__":
    session = requests.Session()
    email="special.one90@hotmail.it"
    password="12345678qwert"
    # walla_go_login(session,email,password)


    # time_start = time.time()
    # # user_agent = ua.getGoogle['useragent']
    # # session = cloudscraper.create_scraper()
    # # session.headers.update({
    # #     "User-Agent": user_agent,
    # # })
    walla_go_login(session)

    # walla_validate(session,mfa_id="",code="")
    # walla_authorize(session,mfa_id='')
    #
    # time_end = time.time()
    #
    # print(f"[*] Working time: {time_end - time_start}")
    #
    # current_time = datetime.now().strftime("%H:%M:%S")
    # print("Текущее время:", current_time)