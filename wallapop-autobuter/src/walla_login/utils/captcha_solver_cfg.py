from datetime import datetime
import os
import sys
import time

from twocaptcha import TwoCaptcha

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
API_2CAPTCHA = os.getenv('API_2CAPTCHA')
SITEKEY = os.getenv('SITEKEY')
PAGE_URL = os.getenv('PAGE_URL')

api_key = os.getenv('APIKEY_2CAPTCHA', API_2CAPTCHA)

solver = TwoCaptcha(api_key)

def solve_wallapop_captcha():
    try:
        result = solver.recaptcha(
            sitekey=SITEKEY,
            url=PAGE_URL,
            enterprise=1
        )
    except Exception as e:
        # sys.exit(e)
        print(f"captcha unsolvable: {e}")

    else:
        # print('solved: ' + str(result))
        code = extract_code_from_result(result)
        # print("Token:", code)

        print(code)
        return code

def extract_code_from_result(result: dict) -> str:
    return result.get("code")

def my_function():
    print(f"Выполняю работу в {datetime.now().strftime('%H:%M:%S')}")

if __name__ == '__main__':
    end_time = time.time() + 600
    counter = 0
    while time.time() < end_time:
        my_function()

        time_s = time.time()
        token = solve_wallapop_captcha()
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"Текущее время: {current_time}")
        time_e = time.time()

        print(f"Solved: {token}")
        print(f"Время решения капчи: {time_e - time_s}")
        counter += 1


        time.sleep(1)
    print(f"Количество решенных капч: {counter}")