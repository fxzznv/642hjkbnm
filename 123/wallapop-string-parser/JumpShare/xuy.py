import json
import random
import re
import uuid

import requests

def generate_guid():
    return str(uuid.uuid4())

def check_walla_duplicate_email(email, password, username, recaptcha_token, depth=0):
    if depth >= 3:
        print("Exceeded maximum retry attempts.")
        return None
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
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        response_text = response.text
        data = json.loads(response_text)
        code_value = data["code"]

        if code_value == "EMAIL_ALREADY_IN_USE":
            return code_value
        return None
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}. Retrying... (attempt {depth + 1}/3)")
        return check_walla_duplicate_email(email, password, username, recaptcha_token, depth=depth + 1)
    except requests.exceptions.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        print(f"Сырой ответ сервера: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None

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
    print("(normalize_accounts): accounts normalized")
    return normalized