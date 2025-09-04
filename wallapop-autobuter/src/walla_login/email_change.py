import random
import time
import uuid
import imaplib
import ssl
import email
from typing import Optional
import re
import requests
from bs4 import BeautifulSoup

from src.logging.logger_init import setup_logger
from src.mail.mail_api import generate_guid
from src.mail.utils.const_mail import COOKIE_DIR
from src.password.reset_password import get_last_email_token

device_id = generate_guid()
mpid = str(random.randint(-2**63, -1))
device_token = generate_guid()
trace_id = uuid.uuid4().hex
span_id = uuid.uuid4().hex[:16]

logger = setup_logger(__name__)

def send_change_email_forbidden(session, auth_token):
    logger.debug("(send_change_email_forbidden): Вход")
    url = "https://api.wallapop.com/api/v3/users/me/email/change"

    headers = {
        "host": "api.wallapop.com",
        "accept-language": "es,ru-RU;q=0.9,ru;q=0.8",
        "mpid": mpid,
        "x-deviceid": device_id,
        "Authorization": f"Bearer {auth_token}",
        "x-devicetoken": device_token,
        "x-deviceos": "1",
        "x-appversion": "10256000",
        "x-semanticversion": "1.256.0",
        "sentry_trace": f"{trace_id}-{span_id}",
        "baggage": f"sentry-environment=production,sentry-public_key=de0e3aa86e91567aa8ee8bee21c5cbe7,sentry-release=com.wallapop%401.256.0%2B10141219,sentry-sample_rand=0.{random.randint(100000000, 999999999)},sentry-trace_id={trace_id}",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.12.0",
    }

    try:
        response = session.post(url, headers=headers, )#json=payload)
        logger.debug(f"(send_change_email_forbidden): Запрос отправлен: {response.status_code}, {response.text}")
        if response.status_code == 403:
            logger.debug(f"(send_change_email_forbidden): Запрос на смену почты отправлен успешно: {response.status_code}, {response.text}")
            print("Status:", response.status_code)
            print("Response:", response.text)
            return response.status_code
        elif response.status_code == 204:
            print("204")
            return response.status_code
        else:
            logger.error(f"(send_change_email_forbidden): Wrong response: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"(send_change_email_forbidden): Exception: {e}")
        print(f"send_change_mail_forbidden: Exception: {e}")
        return None

def send_change_email_approvement(session, auth_token, new_email, password):
    logger.debug("(send_change_email_approvement): Вход")

    url = "https://api.wallapop.com/api/v3/users/me/email"
    payload = {
        "email_address": new_email
    }

    headers = {
        "accept-language": "ru-RU;q=1.0",
        "mpid": mpid,
        "x-deviceid": device_id,
        "Authorization": f"Bearer {auth_token}",
        "x-devicetoken": device_token,
        "x-deviceos": "1",
        "x-appversion": "10256000",
        "x-semanticversion": "1.256.0",
        "sentry_trace": f"{trace_id}-{span_id}",
        "baggage": f"sentry-environment=production,sentry-public_key=de0e3aa86e91567aa8ee8bee21c5cbe7,sentry-release=com.wallapop%401.256.0%2B10141219,sentry-sample_rand=0.{random.randint(100000000, 999999999)},sentry-trace_id={trace_id}",
        "content-type": "application/json; charset=UTF-8",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.12.0",
        "host": "api.wallapop.com"
    }
    
    try:
        response = session.post(url, headers=headers, json=payload)
        logger.info(f"(send_change_email_approvement): Запрос отправлен {response.status_code}, {response.text}")
        if response.status_code == 204:
            print("Status:", response.status_code)
            print("Response:", response.text)
            logger.info(f"(send_change_email_approvement): Успещный status_code: {new_email},{password}")
            return new_email, password
        elif response.status_code == 400:
            return response.status_code, None
        else:
            print(f"(send_change_email_approvement): Wrong response: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"(send_change_email_approvement): Exception: {e}")
        print(f"send_change_email_approvement: {e}")
        return None

def get_mail_change_outlook_token(session, token: str, email_token, puid, canary):
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

    try:
        response = session.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.error(f"(get_mail_change_outlook_token): Status code {response.status_code}: {response.json}")
            print(f"[ERROR] Status code {response.status_code}: {response.json}")
            print(response.text)
            print(response.json())
            print(response.json)
            print(f"Response RAW: {response.text[:1000]}")
            return None
        print(response.text)
        print(response.json())
        print(response.json)
        data = response.json()
        # print(json.dumps(data, indent=2, ensure_ascii=False))
        html_value = data["Body"]["ResponseMessages"]["Items"][0]["Items"][0]["Body"]["Value"]
        soup = BeautifulSoup(html_value, 'html.parser')

        try:
            reset_link = None
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if 'wallapop.com/app/multi-factor/approve' in href:
                    return href
        except:
            reset_link = None
            for link in soup.find_all('a'):
                originalsrc = link.get('originalsrc', '')
                if 'wallapop.com/app/multi-factor/approve' in originalsrc:
                    href = originalsrc
                    return href

        return None

    except Exception as e:
        print(f"get_mail_change_outlook_token: {e}")
        return None

def confirm_walla_change_mail(session, auth_token, approve_token):
    url = "https://api.wallapop.com/api/v3/mfa/approve"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es,en-US;q=0.9,en;q=0.8",
        "Authorization": f"Bearer {auth_token}",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DeviceOS": "0",
        "MPID": mpid,
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "X-AppVersion": "89480",
        "X-DeviceID": generate_guid(),
        "X-DeviceOS": "0",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"'
    }

    data = {
        "approve-token": approve_token
    }

    response = session.post(url, headers=headers, json=data)

    data = response.json()
    if response.status_code != 200:
        print("Invalid response. Thread stopped")
        return None
    print(f"Confirm_walla_change_mail: {response.status_code}, {data}")
    return response.status_code


def walla_change_mail(session, wallapop_session, auth_token, token_json, puid, canary, queries, new_email, password):
    logger.debug("(walla_change_mail): Вход")
    try:
        time.sleep(3)
        forbid_status = send_change_email_forbidden(wallapop_session, auth_token)
        if forbid_status:
            if forbid_status == 403:
                print("403")
                time.sleep(1)

                attempt = 1
                max_attempts = 7

                while attempt <= max_attempts:
                    if attempt < 4:
                        mail_id, sk = get_last_email_token(session=session, canary=canary, token=token_json, puid=puid)
                    else:
                        mail_id, sk = get_last_email_token(session=session, canary=canary, token=token_json, puid=puid,id_number=1)
                    print(f"mail_id: {mail_id}\nsk: {sk}")
                    link = get_mail_change_outlook_token(session=session,token=token_json,email_token=mail_id,puid=puid,canary=canary)
                    print(f"link: {link}")

                    if link:
                        approve_token = link.split("/approve/")[-1]
                        print("approve_token:", approve_token)
                        print(f"(walla_change_mail): Попытка {attempt}, Успех.")
                        wallapop_session.get(f"https://www.wallapop.com/app/multi-factor/approve/{approve_token}")
                        is_confirmation_completed = confirm_walla_change_mail(session, auth_token=auth_token,approve_token=approve_token)
                        if is_confirmation_completed:
                            break
                        return None

                    print(f"(walla_change_mail): Попытка {attempt}, провал. Повтор...")
                    attempt += 1
                    time.sleep(3)
                    if attempt == 7:
                        return None

            yaho_email, new_password = send_change_email_approvement(wallapop_session, auth_token, new_email, password)

            if yaho_email == 400:
                print("(walla_change_mail): Вернуло 400, попытка 2:")
                attempt = 1
                max_attempts = 3
                while attempt <= max_attempts:
                    yaho_email, new_password = send_change_email_approvement(wallapop_session, auth_token, new_email, password)

                    if yaho_email is str:
                        print(f"(walla_change_mail): Попытка {attempt}: Успех")

                        attempt = 1
                        max_attempts = 3
                        while attempt < max_attempts:
                            link = fetch_latest_email(session=session,
                                               imap_server="imap.firstmail.ltd",
                                               username=yaho_email,
                                               password=new_password,
                                               sender_email="info@info.wallapop.com")

                            if link:
                                print(f"Получена ссылка по imap на попытке {attempt}: {link}")
                                approve_token = link.split("/approve/")[-1]
                                print("approve_token:", approve_token)
                                print(f"(walla_change_mail): Попытка {attempt}, Успех.")
                                wallapop_session.get(
                                    f"https://www.wallapop.com/app/multi-factor/approve/{approve_token}")
                                is_confirmation_completed = confirm_walla_change_mail(session, auth_token=auth_token,
                                                                                      approve_token=approve_token)
                                if is_confirmation_completed:
                                    return yaho_email, new_password

                            print(f"Не удалось получить ссылку по imap, попытка {attempt}, повтор..")
                            attempt += 1

                            time.sleep(1)

                        print("По imap не получено письма, расходимся")
                        return None

                    print(f"Попытка {attempt}: Status code: {yaho_email}")
                    attempt += 1

                return None

            attempt = 1
            max_attempts = 3
            while attempt < max_attempts:
                link = fetch_latest_email(session=session,
                                          imap_server="imap.firstmail.ltd",
                                          username=yaho_email,
                                          password=new_password,
                                          sender_email="info@info.wallapop.com")

                if link:
                    print(f"Получена ссылка по imap на попытке {attempt}: {link}")
                    approve_token = link.split("/approve/")[-1]
                    print("approve_token:", approve_token)
                    print(f"(walla_change_mail): Попытка {attempt}, Успех.")
                    wallapop_session.get(f"https://www.wallapop.com/app/multi-factor/approve/{approve_token}")
                    is_confirmation_completed = confirm_walla_change_mail(session, auth_token=auth_token,
                                                                          approve_token=approve_token)
                    if is_confirmation_completed:
                        return yaho_email, new_password


                print(f"Не удалось получить ссылку по imap, попытка {attempt}, повтор..")

                attempt += 1
                time.sleep(1)


            print("По imap не получено письма, расходимся")
            return None

        return None

    except Exception as e:
        logger.error(f"(walla_change_mail): Exception: {e}")
        print(f"walla_change_mail: {e}")
        return None

def fetch_latest_email(session,
    imap_server: str,
    username: str,
    password: str,
    sender_email: str,
    port: int = 993
) -> Optional[str]:

    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    try:
        print(f"Подключение к {imap_server}:{port} саморега {username}...")
        mail = imaplib.IMAP4_SSL(imap_server, port, ssl_context=context)
        mail.login(username, password)
        mail.select("INBOX")

        print(f"Поиск писем от {sender_email}...")
        status, messages = mail.search(None, f'(FROM "{sender_email}")')

        if status != 'OK' or not messages[0]:
            print("Писем от указанного отправителя не найдено")
            return None

        last_email_id = messages[0].split()[-1]

        status, msg_data = mail.fetch(last_email_id, "(RFC822)")

        if status == 'OK' and msg_data and isinstance(msg_data[0], tuple):
            raw_email = msg_data[0][1]
            email_msg = email.message_from_bytes(raw_email)

            html_content = None
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/html":
                        html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                if email_msg.get_content_type() == "text/html":
                    html_content = email_msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            if html_content:
                pattern = r'https?://(?:[a-z]{2}\.)?wallapop\.com/app/multi-factor/approve/[^\s"]+'
                match = re.search(pattern, html_content)
                if match:
                    link = match.group(0)
                    print(f"Найдена ссылка: {link}")

                    # session.get(link)
                    return link
                else:
                    print("Ссылка не найдена в HTML-контенте")
                    return None
            else:
                print("HTML-часть не найдена в письме")
                return None
        else:
            print(f"Ошибка при получении письма с ID {last_email_id}: {status}")
            return None

    except Exception as e:
        print(f"Ошибка: {e}")
        return None
    finally:
        try:
            mail.logout()
        except Exception as e:
            print(f"Ошибка при logout: {e}")
            return None


import os
import json


def save_cookies(new_email, new_password, token, reset_token, wallapop_password, reg_date, reviews, cookie_dir=COOKIE_DIR):
    # Create the cookie directory if it doesn't exist
    os.makedirs(cookie_dir, exist_ok=True)

    base_filename = f"{new_email} {new_password} {wallapop_password} {reg_date} {reviews}"
    extension = ".txt"
    full_path = os.path.join(cookie_dir, base_filename + extension)

    # Prepare the cookies data
    json_payload = [
        {
            "domain": ".wallapop.com",
            "expirationDate": 1762878933502,  # This is a far future date (2025-11-11)
            "httpOnly": False,
            "name": "accessToken",
            "path": "/",
            "sameSite": "lax",
            "secure": True,
            "storeId": None,
            "value": token
        },
        {
            "domain": ".wallapop.com",
            "expirationDate": 1762878933502,
            "httpOnly": True,
            "name": "refreshToken",
            "path": "/",
            "sameSite": "strict",
            "secure": True,
            "storeId": None,
            "value": reset_token
        }
    ]

    # Write the cookies to file
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(json_payload, f, indent=4, sort_keys=True)

    print("Cookies saved successfully")
    return True

if __name__ == "__main__":

    session=requests.Session()
    # send_change_email_forbidden(session, auth_token="q")
    # send_change_email_approvement(session, "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NTkzMTk1OTAiLCJkZXZpY2UiOiJiZjU3YmUyNS1lMzA0LTQyMDYtOTE4MC1hNTQ3ZmRjNjczYjMiLCJpYXQiOjE3NTE3MzU4ODMsImV4cCI6MTc1MTgyMjI4M30.p18oHFRmAFbAk1VgwodO0sdjrmknCM04MC1VC57EDU1w25sd3oAZSo0DLzZP9NMPBWyLLnwewSawS5vB7lSg1Pwy7g9HZM5S8VE7zAOtO41otKnQ45wYCyxGiQBUx1RikaH1i0fc7wYmxfzDPOJ6QyJSwvjgSj_4VtssnTY7YORkk9BxqcMgYWSKVi7-ZscyN5FxF819eVGQTn4XsS3UOC3d2bZJmeDyIWu3i9QuUv1fVpqZOgG36v-LrJl3_GESXfBWRx87tL8VyRBZKcsRG0lgFkZLa1KDCnLpnP6xKQ6ZaLgRX403wo87Ap60M_5DL-8iDHNXlpWVtB70ywkMXQ",
    #                               "sehffdqi@tubermail.com", "123")
    #
    # link = fetch_latest_email(session=session,
    #     imap_server="imap.firstmail.ltd",
    #     username="wyxqsffo@ronaldofmail.com",
    #     password="hekxqdqzS!3549",
    #     sender_email="tutameer@gmail.com"
    # )
    #
    # session.get(link)
    # session.get("https://www.google.com")
    # save_cookies(session=session,new_email="wyxqsffo@ronaldofmail.com",new_password="hekxqdqzS!3549")

    # пк
    auth_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNzY0ODM0OCIsImRldmljZSI6ImM4YjhjN2U0LTlmZTItNGViYS05ZWU2LWM5MjdhYzg2MWUyNSIsImlhdCI6MTc1NTQ2NjY0MSwiZXhwIjoxNzU1NTUzMDQxfQ.Hw-Zb6q1dXeJ4M22wAubFJJnwB-3bGVPxlf3PgS0zM1pRoNcru0nTs8IZgCtnOQlhUPZNd64sOYKEs_qWvP27jmeBEPH5VdFH5WeO-0XgqfIH60TZVnXgrgApHr-amr2IkvTppRJrHEaLZNpuHPFUcutmiF4uiUSgyv6-c26g3V0LegYK47oJiu7td2FXGbW6xoowomPVnRwvCvNfXZta8ZYMvgs7TT9t82n7dQ1vHbJy2NobXHm4y5VvM031ZgY7PSsXN4jQ08AvmfYDbVbEfnNeHh6fadEMnSOWypTnJOoZCv7fblpy2_HFiueuX48OPn3o1HtJiIQ30TDKj_x_Q"
    # приложение на эмуле
    # auth_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0Njg3NDM2NDMiLCJkZXZpY2UiOiJmaFBHQ21kZlNjMmIzbG16NHBjWW1jOjBhNzQyYjM5ODk5MGQ1NmIiLCJpYXQiOjE3NTUxMDgyNTMsImV4cCI6MTc1NTE5NDY1M30.qcvM-AsULL5is3UA8mvLXlRTy54wGLbd9zG05X3rh_kLMQaL6HGqYst2Sg4dStGLFpHiPT7BHUOfZ4ZB9WFWZenfZWlltsPjn30ZoeBA6mXdY-EG3MsXwORQT2kCvxbxnZzzWadOvM5YJBlqsPrJxKfk8Pp9BRmgWVIL3pNY0cw1oIIupdf3FUZV0yExD1YaJVYrRje_oooH3PWiMZwdPH1m0CeKoy9JuWsdDdOmYd_N_jlSZWecFlQubYXBdGMG3hSak0dgtk-bYcWYlkAQHZ7lERCGurIsX00jkbMhaGcrxYvwfzf9TX99KG_uSMgXD9af7nYRpzSRmuxoQGJtRg"
    # телефон но с браузера
    # auth_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0Njg3NDM2NDMiLCJkZXZpY2UiOiIzN2ZmMzA4YS1kNTU5LTRjY2YtYmNjYy01NmIyNzQ2MTA5MmMiLCJpYXQiOjE3NTUxMjc0NDYsImV4cCI6MTc1NTIxMzg0Nn0.zo5hRUzKVDd7FMbXA1ooN5KSuAzghQ5cYKCvcxpslo1-L39oAFEWEAML_VkRXmhg3iNV8WgZB0xXoWB5Bh5VsthCRG5gSB9o3RrG6Tku9J6K-11-BY-rFY7stU-uN2i2vcIrjCc2s0VTUJpeF803ny1PUvfmY-6TSFsEYBeGjLvHxBfu2fdlyrI5VTFKbfIuqhJNxsJGeoHoJUp1QYpiok0An3kCaeWK7170U9X1HvFcBr7FAHvYSo7SOlMHs6hIcqRyIsPyNkNsCNK9Z4T0-smDUYGxJfZjtiqTpm969GxSzsJAs3T_wcxkeXLhsWDYNOB3v8l0HOMjXXVObaGkeg"
    # send_change_email_forbidden(session,auth_token=auth_token)
    send_change_email_approvement(session,auth_token=auth_token,new_email = "aiaiduja@ronaldofmail.com", password = "utafmypvY!8410")