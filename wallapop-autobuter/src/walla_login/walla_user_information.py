from datetime import datetime

from src.walla_login.utils.walla_login_constants import MPID, DEVICE_ID

def get_user_reviews_count(session, auth_token):
    url = "https://api.wallapop.com/api/v3/users/me/stats"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6,be;q=0.5,tg;q=0.4",
        "Authorization": f"Bearer {auth_token}",
        "Connection": "keep-alive",
        "DeviceOS": "0",
        "Host": "api.wallapop.com",
        "MPID": MPID,
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "X-AppVersion": "87130",
        "X-DeviceID": DEVICE_ID,
        "X-DeviceOS": "0",
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    try:
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            reviews_count = None
            for r in data.get("counters", []):
                if r.get("type") == "reviews":
                    reviews_count = r.get("value")
                    return reviews_count
            else:
                print("Параметр 'reviews' не найден")
                return None
        else:
            print("Ошибка запроса:", response.status_code)
            print(response.text)
            return None

    except Exception as e:
        print("<UNK> <UNK>:", e)
        return None

def get_registration_date(session, auth_token):
    url = "https://api.wallapop.com/api/v3/users/me/"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6,be;q=0.5,tg;q=0.4",
        "Authorization": f"Bearer {auth_token}",
        "Connection": "keep-alive",
        "DeviceOS": "0",
        "Host": "api.wallapop.com",
        "MPID": MPID,
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "X-AppVersion": "87100",
        "X-DeviceID": DEVICE_ID,
        "X-DeviceOS": "0",
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    try:
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            register_ts = data.get("register_date")
            if register_ts:
                readable_date = datetime.fromtimestamp(register_ts / 1000).strftime("%Y-%m-%d")  #%H:%M:%S
                print("registered:", readable_date)
                return readable_date
            else:
                print("field register not found")
                return None
        else:
            print("Bad request:", response.status_code)
            print(response.text)
            return None
    except Exception as e:
        print("<UNK> <UNK>:", e)
        return None


def get_wallet_balance(session, auth_token):
    url = "https://api.wallapop.com/api/v3/payments/wallets/main"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6,be;q=0.5,tg;q=0.4",
        "authorization": f"Bearer {auth_token}",
        "Connection": "keep-alive",
        "DeviceOS": "0",
        "Host": "api.wallapop.com",
        "mpid": MPID,
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "X-AppVersion": "87100",
        "X-DeviceOS": "0",
        "x-deviceid": DEVICE_ID,
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
    }
    try:
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            amount = data.get("amount")
            currency = data.get("currency")
            blocked = data.get("blocked")

            if not blocked:
                print(f"{amount} {currency}")
            else:
                print(f"{amount} {currency} - BLOCKED")

            wallet_info_str = f'{amount} {currency}'
            return wallet_info_str
        else:
            print("Ошибка запроса:", response.status_code)
            print(response.text)
            return None
    except Exception as e:
        return None

def get_all_user_information(session, auth_token):
    try:
        reg_date = get_registration_date(session, auth_token)
        balance = get_wallet_balance(session, auth_token)
        reviews = get_user_reviews_count(session, auth_token)

        return reg_date, balance, reviews
    except Exception as e:
        print("get_all_user_information failed:", e)
        return None

# if __name__ == '__main__':
#     reg = get_registration_date()
#     wallet = get_wallet_balance()
#     rating = get_user_rate()
#     rew = get_user_rewiews_count()
#
#     print(f'some_email:pass | {reg} | {wallet} | {rating}✯ ({rew})')
