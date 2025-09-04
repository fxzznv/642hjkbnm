import json
import logging
import random
import uuid

import requests
from fake_useragent import UserAgent
from src.logging.logger_init import setup_logger
from src.mail.utils.const_mail import CSV_FILE_PATH

logger = setup_logger(__name__)
ua = UserAgent()


def generate_guid():
    return str(uuid.uuid4())

def is_null_or_empty(s):
    return s is None or s == ''

def get_junk_email_configuration(session,  canary: str, token: str):
    logger.info("Начало get_junk_email_configuration:")
    url = 'https://outlook.live.com/owa/0/service.svc?action=GetMailboxJunkEmailConfiguration&app=Mail&n=57'

    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'action': 'GetMailboxJunkEmailConfiguration',
        'authorization': f'MSAuth1.0 usertoken="{token}", type="MSACT"',
        'cache-control': 'no-cache',
        'content-length': '0',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://outlook.live.com',
        'pragma': 'no-cache',
        'prefer': 'exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        'priority': 'u=1, i',
        'referer': 'https://outlook.live.com/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'x-owa-hosted-ux': 'false',
        'x-owa-sessionid': generate_guid(),
        'x-req-source': 'Mail',
        'x-owa-canary': canary,
    }

    response = session.post(url, headers=headers, json={})
    if response.status_code == 204:
        logger.error("(get_junk_email_configuration): Ответ 204: нет содержимого.")
        print("Ответ 204: нет содержимого.")
        return None
    if response.status_code == 200:
        logger.debug("(get_junk_email_configuration): Запрос успешен. Конфигурация фильтрации спама:")
        try:
            logger.debug("(get_junk_email_configuration): Разбор json успешен")
            data = response.json()
            blocked_senders = data["Options"]["BlockedSendersAndDomains"]

            # print(data["Options"]["BlockedSendersAndDomains"])
            # print(type(data["Options"]["BlockedSendersAndDomains"]))

            if "info@info.wallapop.com" in blocked_senders:
                return data
            return None
        except ValueError:
            logger.error("(get_junk_email_configuration): Ошибка при разборе JSON.")
            print("Ошибка при разборе JSON.")
            return None
    else:
        logger.error(f"(get_junk_email_configuration): Ошибка: код {response.status_code} '\t' Ответ сервера:, {response.text}")
        print(f"Ошибка: код {response.status_code}")
        print("Ответ сервера:", response.text)
        return None

def get_contacts_trusted(session, canary: str, token: str):
    logger.info("Начало get_junk_email_configuration:")
    url = 'https://outlook.live.com/owa/0/service.svc?action=GetMailboxJunkEmailConfiguration&app=Mail&n=57'

    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'action': 'GetMailboxJunkEmailConfiguration',
        'authorization': f'MSAuth1.0 usertoken="{token}", type="MSACT"',
        'cache-control': 'no-cache',
        'content-length': '0',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://outlook.live.com',
        'pragma': 'no-cache',
        'prefer': 'exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        'priority': 'u=1, i',
        'referer': 'https://outlook.live.com/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'x-owa-hosted-ux': 'false',
        'x-owa-sessionid': generate_guid(),
        'x-req-source': 'Mail',
        'x-owa-canary': canary,
    }

    response = session.post(url, headers=headers, json={})
    if response.status_code == 204:
        logger.error("(get_junk_email_configuration): Ответ 204: нет содержимого.")
        print("Ответ 204: нет содержимого.")
        return None
    if response.status_code == 200:
        logger.debug("(get_junk_email_configuration): Запрос успешен. Конфигурация фильтрации спама:")
        try:
            logger.debug("(get_junk_email_configuration): Разбор json успешен")
            data = response.json()
            # print(json.dumps(data, indent=4, ensure_ascii=False))  # красивый вывод JSON
            is_contacts_trusted = data["Options"]["ContactsTrusted"]
            if is_contacts_trusted:
                # print('a')
                return data
            return None
        except ValueError:
            logger.error("(get_junk_email_configuration): Ошибка при разборе JSON.")
            print("Ошибка при разборе JSON.")
            return None
    else:
        logger.error(f"(get_junk_email_configuration): Ошибка: код {response.status_code} '\t' Ответ сервера:, {response.text}")
        print(f"Ошибка: код {response.status_code}")
        print("Ответ сервера:", response.text)
        return None

def set_contacts_trusted(session, canary: str, token: str):
    logger.info("Начало set_junk_email_configuration:")
    url = 'https://outlook.live.com/owa/0/service.svc?action=SetMailboxJunkEmailConfiguration&app=Mail&n=57'

    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'action': 'SetMailboxJunkEmailConfiguration',
        'authorization': f'MSAuth1.0 usertoken="{token}", type="MSACT"',
        'cache-control': 'no-cache',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://outlook.live.com',
        'pragma': 'no-cache',
        'prefer': 'exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        'priority': 'u=1, i',
        'referer': 'https://outlook.live.com/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'x-owa-hosted-ux': 'false',
        'x-owa-sessionid': generate_guid(),
        'x-req-source': 'Mail',
        'x-owa-canary': canary,
    }

    payload = {
        "__type": "SetMailboxJunkEmailConfigurationRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "Options": {
            "ContactsTrusted": True,
        }
    }
    response = session.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        logging.info("(set_junk_email_configuration): Успешно обновлена конфигурация JunkEmailConfiguration")
        return response.json()
    else:
        logging.error(f"(set_junk_email_configuration): Ошибка при обновлении конфигурации JunkEmailConfiguration: {response.status_code}")
        return None

def wallapop_bypass(session, access_token):
    csv_file_path = CSV_FILE_PATH

    with open(csv_file_path, "rb") as f:
        csv_bytes = list(f.read())

    payload = {
        "__type": "ImportContactListRequest:#Exchange",
        "Header": {
            "__type": "JsonRequestHeaders:#Exchange",
            "RequestServerVersion": "V2018_01_08",
            "TimeZoneContext": {
                "__type": "TimeZoneContext:#Exchange",
                "TimeZoneDefinition": {
                    "__type": "TimeZoneDefinitionType:#Exchange",
                    "Id": "Greenwich Standard Time"
                }
            }
        },
        "ImportedContactList": {
            "CSVData": csv_bytes
        }
    }

    # URL запроса
    url = "https://outlook.live.com/owa/0/service.svc?action=ImportContactList&UA=0&app=People&n=175"

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru-RU,ru;q=0.9",
        "action": "ImportContactList",
        "authorization": f'MSAuth1.0 usertoken="{access_token}", type="MSACT"',
        "content-type": "application/json; charset=utf-8",
        "origin": "https://outlook.live.com",
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "referer": "https://outlook.live.com/",
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "'Windows'",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "x-owa-correlationid": generate_guid(),
        "x-owa-sessionid": generate_guid(),
    }

    try:
        response = session.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            logger.info(f"(wallapop bypass): обход выполнен: {response.status_code}, {response.text}")
            print("[*]Обнаружен скрипт, выполнен обход")
            return data
        else:
            logger.error(f"(wallapop bypass): Запрос вернул неправильный ответ: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"(wallapop bypass: Response error: {e}")
        return None

def search_custom_emails(session, canary: str, token, queries: list[str]):
    logger.info("Начало search_custom_emails:")
    url = 'https://outlook.live.com/searchservice/api/v2/query'

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US',
        'authorization': f'MSAuth1.0 usertoken="{token}", type="MSACT"',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://outlook.live.com',
        'pragma': 'no-cache',
        'prefer': 'exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        'priority': 'u=1, i',
        'referer': 'https://outlook.live.com/',
        'scenariotag': '1stPg_cv',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-client-flights': 'OWA_BestMatch_V15,...,querymicroservice',
        'x-ms-appname': 'owa-reactmail',
        'x-owa-canary': canary,
        'x-owa-hosted-ux': 'false',
        'x-req-source': 'Mail',
        'x-search-griffin-version': 'GWSv2',
    }

    cleaned_queries = list({q.strip().lower() for q in queries if q.strip()})

    query_parts = []
    for q in cleaned_queries:
        if '@' in q:
            query_parts.append(f'from:({q})')
        else:
            query_parts.append(f'from:(*{q})')  # wildcard по домену

    query_string = ' OR '.join(query_parts)

    payload = {
        "Cvid": generate_guid(),
        "Scenario": {"Name": "owa.react"},
        "TimeZone": "SA Pacific Standard Time",
        "TextDecorations": "Off",
        "EntityRequests": [
            {
                "EntityType": "Conversation",
                "ContentSources": ["Exchange"],
                "Filter": {
                    "Or": [
                        {"Term": {"DistinguishedFolderName": "msgfolderroot"}},
                        {"Term": {"DistinguishedFolderName": "DeletedItems"}}
                    ]
                },
                "From": 0,
                "Query": {
                    "QueryString": f"({query_string})",
                    "DisplayQueryString": "",
                    "ClientQueryAlterationReasons": "PeopleSearch Scenario"
                },
                "RefiningQueries": None,
                "Size": 25,
                "Sort": [
                    {"Field": "Score", "SortDirection": "Desc", "Count": 3},
                    {"Field": "Time", "SortDirection": "Desc"}
                ],
                "EnableTopResults": True,
                "TopResultsCount": 3
            }
        ],
        "QueryAlterationOptions": {
            "EnableSuggestion": True,
            "EnableAlteration": True,
            "SupportedRecourseDisplayTypes": [
                "Suggestion", "NoResultModification", "NoResultFolderRefinerModification", "NoRequeryModification",
                "Modification"
            ]
        }
    }

    response = session.post(url, headers=headers, json=payload)
    logger.info(f"(search_custom_emails): Статус код: {response.status_code}")
    data = response.json()

    total = data['EntitySets'][0]['ResultSets'][0]['Total']
    # print(total)
    # print(data)
    return response.json()

def check_walla_duplicate_email(email, password, username, recaptcha_token):
    url = "https://api.wallapop.com/api/v3/access/email"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6,be;q=0.5,tg;q=0.4",
        "content-type": "application/json",
        "deviceos": "0",
        "mpid": str(random.randint(-2**63, -1)),
        "referer": "https://es.wallapop.com/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "x-appversion": "88180",
        "x-deviceid": generate_guid(),
        "x-deviceos": "0"
    }

    payload = {
        "email_address": email,
        "password": password,
        "username": username,
        "user_settings": {
            "accepted_comms": False,
            "accepted_terms": True},
        "metadata": {
            "session_id": generate_guid(),
            "recaptcha_token": recaptcha_token
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        # print(f"Статус ответа: {response.status_code}")
        # print(f"Содержимое ответа: {response.text}")
        response_text = response.text
        data = json.loads(response_text)
        code_value = data["code"]

        print(f"{email}: Значение ключа 'code': {code_value}")

        if code_value == "EMAIL_ALREADY_IN_USE":
            return code_value
        return None
    except requests.exceptions.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        print(f"Сырой ответ сервера: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None





if __name__ == "__main__":

    session = requests.Session()
    auth_token = "EwAIBOl3BAAUxG8T4TQNdaMKj7W5hdXgD68HTzwAAV9dxJcV4tBy2929i2eK25dcRw9CU28UToeB6CUQS4bH2HSGBwC5Qq/W7cyzG5VNEhvZmyUps2AnlevOIF2JUrXbKVwyufXPt3kzxdGxOYJG02Vd2Id36M+slUDmev5k9Zg2SJDJhI2YwR7E6w679Siyelb6Z+Vp2glHegclRZORcdauIIbMNbTGFNGLybHJyu58nBKTk2ROd2XKOvTAd/IkBwiy21zxBFimRRdwPYyR6MgGVu+NZ2kcQiBqKLFUlqB50K8G66FLtZn/Pi5o8qT4yZMpIH+UxYqeKzqDNRu5XB7fCP8UPkaOSl32U94NV4Vy8yNXmCahtGQOGWLheH0QZgAAEKHrT/0+L2+kVzK51nAAOn3QAlXTZf0hM5j4pinFJ1EnnHL25YWa0OgKK5d169EPMQI4dzwJ0pRxYx0kQyQI6DpTWMT14whqOlaTqyW…khrIYY3FYzSEyp6g67mKeX1rA79HfrGNcRTlEvojdVV3heMbO8Obb+LGBU37SMV59Snn5M6tbQ/ZM6p/s8Dh4Bf2wkSpgKNhXLZ3qtjxnQkJyNt4o6sh5IT+TJkWea1/5IXT5HYtzan7PA0GKIUlG8BJhTfWC/wChMR9cAp/tG1mJ52IgqJIVUCIhVAhhvLjMX1IlsIEbASuUVGuONCpR508ERsXoDJCUoqx9gVsQOXbDBrX0dQHAjrlhvsBDayGJz4bVWFM5uLPqslylz20JFg+cj1WvWIhehKo85OcPml0mGp+ZxbPwLmP1FxBXhU9PJ4oE6wAaYEAQIk5jb2qVlMt3tDqmKL24k+EUF5Fld2MrMSuqPMTRmtGIwIVqejzExGZdOiy/PSh7ZqMwVkVww+Y5nDy1fB1lJJWOCar7fZXPvWu56xVEtXM/FVRLUSg6h0fJ8RG3ogH6ApJd5CpPr1rKaQcJdxJ/jk0GoQ7FL+y6xoD"
    inbox_folderid = "AQMkADAwATYwMAItNjFkYy1kNjBmLTAwAi0wMAoALgAAAziy7bwSGdZGpzG3It1JTRwBAHjf1Zl7metKg4q5mIZhsxgAAAIBDAAAAA=="
    deleted_folderid = ""
    # create_inbox_rule(session, auth_token, inbox_folderid)
    # extract_puid_tenatid(id_token=None)
    # get_oulook_folders(auth_token)