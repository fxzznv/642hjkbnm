import os
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def get_last_jumpshare_link(depth=0):
    url = "https://raw.githubusercontent.com/tpr297/redirect/main/link.txt"

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://tpr297.github.io",
        "priority": "u=1, i",
        "referer": "https://tpr297.github.io/",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            links = response.text.strip().split('\n')
            if links:
                last_link = links[-1].strip()
                print("Последняя ссылка:", last_link)
                return last_link
            else:
                if depth == 4:
                    print("Ссылка не была получена после 4 попыток")
                    return None
                print("Ссылки не найдены,пробуем ещё раз..")
                time.sleep(5)
                get_last_jumpshare_link(depth+1)

        else:
            print("Ошибка запроса:", response.status_code)
            return None
    except Exception as e:
        print(f"Failed request: {response.status_code},{response.text}: {e}")
        return None

def parse_jumpshare_strings(link, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)  # Передаем опции в драйвер
    try:
        driver.get(link)

        # Ввод пароля
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#passcode"))
        )
        password_field.send_keys(password)

        # Нажатие кнопки submit
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit"))
        )
        submit_button.click()

        # Ожидание загрузки
        time.sleep(2)  # Лучше заменить на ожидание конкретного элемента

        # Прокрутка вниз (предполагается, что функция scroll_to_bottom определена)
        scroll_to_bottom(driver)

        # Получение содержимого pre-элемента
        pre_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        pre_content = pre_element.text

        # Сохранение в файл
        file_path = "1.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pre_content if pre_content else "")

        # Проверка создания файла
        if os.path.exists(file_path):
            print(f"Файл '{file_path}' успешно создан.")
            return True
        else:
            print(f"Ошибка: файл '{file_path}' не создан.")
            return None

    finally:
        driver.quit()

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.05)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

if __name__ == "__main__":
    parse_jumpshare_strings(link="https://jumpshare.com/s/oPPoaSirzy6p4YQlUZzT", password="SEm1ZFzUn0InTQXmHUNa4R")