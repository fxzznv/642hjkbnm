import json
import time
from pymongo import MongoClient


def init_mongo():
    try:
        client = MongoClient('mongodb://root:xuecocNo1@127.0.0.1:27017/?authSource=admin')
        db = client['samoregi_db']
        collection = db['processed_accounts']
        # Тест подключения (опционально, можно у
        return collection
    except Exception as e:
        print(f"Ошибка подключения к MongoDB: {e}")
        raise


def save_string_and_cookies(accessToken, resetToken, samoreg):
    collection = init_mongo()

    json_payload = [
        {
            "domain": ".wallapop.com",
            "expirationDate": 1762878933502,
            "httpOnly": False,
            "name": "accessToken",
            "path": "/",
            "sameSite": "lax",
            "secure": True,
            "storeId": None,
            "value": accessToken
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
            "value": resetToken
        }
    ]

    # Создание строки JSON для cookies_txt
    cookies_txt = json.dumps(json_payload, indent=4, sort_keys=True)

    try:
        document = {
            "samoreg": samoreg,
            "cookies_txt": cookies_txt,
            "created_at": time.time()
        }
        result = collection.insert_one(document)
        print(f"Сохранено для _id {result.inserted_id}: samoreg={samoreg}, cookies_txt={cookies_txt[:50]}...")
        return result.inserted_id
    except Exception as e:
        print(f"Ошибка сохранения в MongoDB: {e}")
        raise


def get_recent_records(hours=24):
    """
    Получает записи за последние N часов
    """
    collection = init_mongo()

    try:
        time_threshold = time.time() - (hours * 3600)
        records = list(collection.find({"created_at": {"$gte": time_threshold}}))
        print(f"Записей за последние {hours} часов: {len(records)}")
        return records
    except Exception as e:
        print(f"Ошибка при получении recent records: {e}")
        raise


def show_recent_records_simple(hours=24):
    """
    Простой вывод записей за последние N часов
    """
    collection = init_mongo()

    try:
        time_threshold = time.time() - (hours * 3600)
        records = list(collection.find({"created_at": {"$gte": time_threshold}}))

        print(f"\n=== ЗАПИСИ ЗА ПОСЛЕДНИЕ {hours} ЧАСОВ ===")
        print(f"Всего записей: {len(records)}")

        for record in records:
            print(f"\n• Samoreg: {record.get('samoreg')}")
            print(f"• Время: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.get('created_at')))}")

            # Показываем только accessToken и refreshToken
            cookies_txt = record.get('cookies_txt', '')
            if cookies_txt:
                try:
                    cookies_data = json.loads(cookies_txt)
                    for cookie in cookies_data:
                        if cookie['name'] in ['accessToken', 'refreshToken']:
                            print(f"• {cookie['name']}: {cookie['value'][:20]}...")
                except:
                    print("• Cookies: (не удалось распарсить)")

        return records

    except Exception as e:
        print(f"Ошибка: {e}")
        raise


# Быстрый вызов


def main():
    # Инициализация MongoDB
    collection = init_mongo()
#
#     # Пример данных
#     samoreg = "12345@gmail.com:123pass123"
#     cookies_txt = """new_email:new_pass:token123:reset_token456:wallapop_pass:2023-01-01:5
# another_cookie_line:more_data
# # Комментарий в файле cookies
# extra_field:value"""
#
#     save_string_and_cookies("123","321","12345@gmail.com:123pass123")
    show_recent_records_simple(24)

    # Сохранение
    # try:
    #     inserted_id = save_string_and_cookies(collection, samoreg, cookies_txt)
    #     print(f"Сохранено с _id: {inserted_id}")
    # except Exception as e:
    #     print(f"Ошибка в main: {e}")


if __name__ == "__main__":
    main()