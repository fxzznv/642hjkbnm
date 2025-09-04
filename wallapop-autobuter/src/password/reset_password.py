import random
import secrets
import string
import time
from bs4 import BeautifulSoup

from src.mail.mail_api import generate_guid
from src.logging.logger_init import setup_logger
from src.password.utils.const_password import RESET_PASSWORD_INITIAL_DELAY, RESET_PASSWORD_MAX_ATTEMPTS

logger = setup_logger(__name__)


def get_last_email_token(session, canary: str, token: str, puid, id_number=0):
    logger.info("Запуск get_last_email_token")
    url = "https://outlook.live.com/searchservice/api/v2/query?n=96&cv=5P8X3B9W64IBN3k7AzU%2FTA.109"

    headers = {
        "accept": "*/*",
        "accept-language": "ru-RU",
        "authorization": f'MSAuth1.0 usertoken="{token}", type="MSACT"',
        "client-request-id": generate_guid(),
        "client-session-id": generate_guid(),
        "content-type": "application/json",
        "ms-cv": generate_guid(),
        "origin": "https://outlook.live.com",
        "owaappid": generate_guid(),
        "prefer": 'IdType="ImmutableId", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders", exchange.behavior="IncludeThirdPartyOnlineMeetingProviders"',
        "priority": "u=1, i",
        "referer": "https://outlook.live.com/",
        "scenariotag": "1stPg_mg",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-anchormailbox": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-client-flights": "OWA_BestMatch_V15,CalendarInsightsFlight,EESForEmailConv,EESForEmailConvSsa,EnableTidBits,EnableTidBits2,PopulateTidBits,PopulateTidBits2",
        # "x-client-localtime": "2025-08-20T19:38:03.050-04:00",
        # "x-clientid": "A62916457AC9422D8B3B776BBD6DB516",
        "x-ms-appname": "owa-reactmail",
        "x-owa-canary": canary,
        "x-owa-hosted-ux": "false",
        "x-owa-sessionid": generate_guid(),
        "x-req-source": "Mail",
        "x-routingparameter-sessionkey": f"PUID:{puid}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa",
        "x-search-griffin-version": "GWSv2",
        "x-tenantid": "84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa, 84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa"
    }

    payload = {
        "Cvid": generate_guid(),
        "Scenario": {"Name": "owa.react"},
        "TimeZone": "SA Western Standard Time",
        "TextDecorations": "Off",
        "EntityRequests": [
            {
                "EntityType": "Message",
                "ContentSources": ["Exchange"],
                "Filter": {
                    "Or": [
                        {"Term": {"DistinguishedFolderName": "msgfolderroot"}},
                        {"Term": {"DistinguishedFolderName": "DeletedItems"}}
                    ]
                },
                "From": 0,
                "Query": {"QueryString": "info@info.wallapop.com"},
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
                "Suggestion",
                "NoResultModification",
                "NoResultFolderRefinerModification",
                "NoRequeryModification",
                "Modification"
            ]
        },
        "LogicalId": generate_guid()
    }

    logger.debug(f"Отправка запроса на {url} с заголовками: {headers} и телом: {payload}")

    try:
        response = session.post(url, headers=headers, json=payload)
        logger.info(f"Статус ответа: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"(get_last_email_token): ERROR: {response.status_code}, ответ: {response.text[:500]}")
            # print(f"[ERROR] Статус {response.status_code}: {response.text[:500]}")
            return None, response.status_code

        data = response.json()
        logger.debug(f"Данные ответа: {data}")

        try:
            first_result = data["EntitySets"][0]["ResultSets"][0]["Results"][id_number]
            email_id = first_result["Id"]
            logger.info(f"Успех - email_id: {email_id}")
            # print(f"[SUCCESS] email_id: {email_id}")
            return email_id, response.status_code
        except (KeyError, IndexError) as e:
            logger.warning(f"Письма не найдены или неверный формат ответа: {e}")
            # print(f"[WARN] Письма не найдены или неверный формат ответа: {e}")
            return None,response.status_code
    except Exception as e:
        logger.error(f"Ошибка в get_last_email_token: {e}")
        # print(f"[ERROR] get_last_email_token: {e}")
        return None

def get_wallapop_reset_token(session, token: str, email_token, email, puid):
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
            logger.error(f"(get_html_from_conversation): Status code {response.status_code}: {response.json}")
            print(f"[ERROR] Status code {response.status_code}: {response.json}")
            return None
        data = response.json()
        print(data)
        # print(json.dumps(data, indent=2, ensure_ascii=False))
        html_value = data["Body"]["ResponseMessages"]["Items"][0]["Items"][0]["Body"]["Value"]
        soup = BeautifulSoup(html_value, 'html.parser')
        try:
            reset_link = None
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if 'wallapop.com/password' in href:
                    reset_link = href
        except:
            reset_link = None
            for link in soup.find_all('a'):
                originalsrc = link.get('originalsrc', '')
                if 'wallapop.com/password' in originalsrc:
                    reset_link = originalsrc

        if reset_link:
            logger.debug(f"(get_html_from_conversation): Ссылка на сброс пароля от Wallapop: {reset_link}")
            print(f"{email}: Ссылка на сброс пароля от Wallapop: {reset_link}")
            token = reset_link.split('/password/')[-1]
            logger.debug(f"(get_html_from_conversation): Токен: {token}")
            print("Токен:", token)
            return token
        else:
            logger.error(f"(get_html_from_conversation): Ссылка на сброс пароля не найдена.")
            print("Ссылка на сброс пароля не найдена.")
        return None
    except Exception as e:
        print(f"get_wallapop_reset_token: {e}")
        return None

def generate_random_password(length=random.randint(8,15)):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def pass_reset(session, token):
    url = 'https://api.wallapop.com/shnm-portlet/api/v1/access.json/passwordRecovery/update'

    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip, deflate, br, zstd",
        "Accept-language": "en-US;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Deviceos": "0",
        "Host": "api.wallapop.com",
        "Mpid": str(random.randint(-2**63, -1)),
        "Origin": "https://uk.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        "Sec-ch-ua": '"Google Chrome";v="135", "Chromium";v="135", "Not/A)Brand";v="24"',
        "Sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-appversion": "87310",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    }

    password = generate_random_password()
    payload = {
        'password': password,
        'token': token,
    }
    try:
        response = session.post(url, headers=headers, data=payload)

        if response.status_code != 204:
            logger.error(f"(pass_reset): ERROR: Status code {response.status_code}: {response.json()}")
            print(f"[ERROR] Status code {response.status_code}: {response.json}")
            return None
        else:
            logger.debug(f"(pass_reset): Пароль успешно изменен на : {password}")
            print(f"[+] Пароль успешно изменен на : {password}")
            return password
    except Exception as e:
        print(f"(pass_reset): ERROR: {e}")
        return None


def reset_walla_password(session, wallapop_session, canary, token, raw_email, puid):
    try:
        time.sleep(3)
        attempts = 1
        delay = RESET_PASSWORD_INITIAL_DELAY
        while attempts <= RESET_PASSWORD_MAX_ATTEMPTS:
            mail_token, mail_search_status_code = get_last_email_token(session=session, canary=canary, token=token,puid=puid)
            if mail_token:
                print(f"(reset_walla_password): Попытка хука сброса пароля {attempts}. Токен найден")
                reset_token = get_wallapop_reset_token(session=session, token=token, email_token=mail_token,email=raw_email, puid=puid)
                new_password = pass_reset(session=wallapop_session, token=reset_token)
                if new_password:
                    print(f"Пароль успешно изменен")
                    return new_password

            print(f"(reset_walla_password): Попытка хука сброса пароля {attempts}. Провал")
            attempts += 1
            time.sleep(3)

        raise NotImplementedError("Исключение. Блок reset_password лёг. ")

    except ValueError as e:
        print(f"(pass_reset): ERROR: {e}")
        return None
