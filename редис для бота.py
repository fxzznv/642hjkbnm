import redis


def push_samoregs_from_file(filepath: str, n: int):
    """
    Загружает первые n строк из файла в Redis список 'samoregi:list' и удаляет их из файла.
    Выводит содержимое списка Redis после загрузки.

    Args:
        filepath (str): Путь к файлу samoregi.txt
        n (int): Количество строк для загрузки
    """
    redis_client = redis.Redis(
        host="62.60.246.153",
        port=6379,
        decode_responses=True,
        password="xuecocNo1"
    )

    try:
        # Читаем все строки из файла
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            all_samoregs = [line.strip() for line in f.readlines() if line.strip()]

        if not all_samoregs:
            print(f"Файл {filepath} пуст")
            return

        # Берём первые n строк
        n = min(n, len(all_samoregs))  # Не больше, чем есть в файле
        samoregs_to_push = all_samoregs[:n]

        if not samoregs_to_push:
            print(f"Нет строк для загрузки (n={n})")
            return

        # Пушим строки в Redis
        redis_client.delete("samoregi:list")  # Очищаем список (опционально, уберите, если не нужно)
        redis_client.lpush("samoregi:list", *samoregs_to_push)
        print(f"Успешно загружено {len(samoregs_to_push)} саморегов в Redis")

        # Удаляем использованные строки из файла
        remaining_samoregs = all_samoregs[n:]
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in remaining_samoregs:
                f.write(line + '\n')
        print(f"Удалено {len(samoregs_to_push)} строк из файла {filepath}. Осталось строк: {len(remaining_samoregs)}")

        # Выводим содержимое списка Redis
        redis_list = redis_client.lrange("samoregi:list", 0, -1)
        if redis_list:
            print("Содержимое списка 'samoregi:list' в Redis:")
            for i, samoreg in enumerate(redis_list, 1):
                print(f"{i}. {samoreg}")
        else:
            print("Список 'samoregi:list' в Redis пуст")

    except FileNotFoundError:
        print(f"Файл {filepath} не найден")
    except PermissionError:
        print(f"Ошибка доступа к файлу {filepath}")
    except redis.RedisError as re:
        print(f"Ошибка Redis: {re}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


# Пример использования
if __name__ == "__main__":
    filepath = "wallapop-autobuter/input/samoregi.txt"  # Укажите путь к вашему файлу
    n = 200  # Количество строк для загрузки
    push_samoregs_from_file(filepath, n)