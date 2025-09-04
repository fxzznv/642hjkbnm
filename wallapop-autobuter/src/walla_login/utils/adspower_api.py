# """
# Actions:
# 1. Create  profile
# 2. Delete profile
# 3. Open Browser
# 4. Close Browser
# 5. Check connection status
# 6. Check browser status
# """
# import os
# import random
# import time
# import uuid
# import requests
# from dotenv import load_dotenv
# from playwright.sync_api import sync_playwright
# from twocaptcha import TwoCaptcha
#
# load_dotenv()
#
# ADSPOWER_API_KEY = os.getenv('ADSPOWER_API_KEY')
# ADSPOWER_HOST = os.getenv('ADSPOWER_HOST')
#
# def check_connection_status():
#     url = f"{ADSPOWER_HOST}/status"
#     response = requests.get(url)
#
#     print(response.status_code, response.json())
#
# mobile_ua_list = [
#     # iPhone
#     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
#     "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
#
#     # Android
#     "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
#     "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
#
#     # iPad
#     "Mozilla/5.0 (iPad; CPU OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
# ]
#
# def get_mobile_resolution(ua: str) -> str:
#     # iPhone (разрешения реальных моделей)
#     if "iPhone" in ua:
#         return random.choice([
#             "375_812",  # iPhone X/XS/11 Pro
#             "414_896",  # iPhone 11/XR
#             "390_844",  # iPhone 12/13/14
#             "428_926"  # iPhone 12/13/14 Pro Max
#         ])
#
#     # iPad
#     elif "iPad" in ua:
#         return random.choice([
#             "768_1024",  # Стандартный iPad
#             "810_1080",  # iPad Mini 6
#             "834_1194"  # iPad Pro 11"
#         ])
#
#     # Android (Samsung/Google Pixel)
#     else:
#         return random.choice([
#             "360_800",  # Samsung S20/S21
#             "412_915",  # Pixel 6/7
#             "393_873",  # Samsung S22/S23
#             "430_932"  # Samsung S23 Ultra
#         ])
#
# def generate_fingerprint():
#     ua = random.choice(mobile_ua_list)
#     stable_versions = ["131", "133", "135", "137"]
#
#     return {
#         "ua": ua,
#         "screen_resolution": get_mobile_resolution(ua),
#         "language": ["es-ES", "es"] if random.random() > 0.5 else ["en-US", "en"],
#         "canvas": "1",
#         "webgl_image": "1",
#         "webgl": "3",
#         "audio": "1",
#         "client_rects": "1",
#         "hardware_concurrency": str(random.choice([2, 4])),
#         "device_memory": str(random.choice([2, 4, 6])),
#         "device_name_switch": "1",
#         "fonts": random.choice([
#             ["Arial", "Segoe UI", "Tahoma"],
#             ["Roboto", "Open Sans", "Ubuntu"],
#             ["Georgia", "Times New Roman"]
#         ]),
#         "mac_address_config": {"model": "1"},
#         "browser_kernel_config": {
#             "type": "chrome",
#             "version": random.choice(stable_versions)
#         },
#         "random_ua": {
#             "ua_browser": ["chrome"],
#             "ua_version": stable_versions,
#             "ua_system_version": ["Android 13", "iOS 16"]
#         }
#     }
#
# def create_adspower_profile(user_proxy_cfg):
#     url = f"{ADSPOWER_HOST}/api/v2/browser-profile/create"
#     fingerprint_cfg = generate_fingerprint()
#
#     payload = {
#         "name": f"wallapop_{uuid.uuid4().hex[:6]}",
#         "group_id": "0",
#         "platform": "es.wallapop.com",
#         "repeat-config": [0],
#         "tabs": ["https://www.google.com"],
#         "user_proxy_config": user_proxy_cfg,
#         "fingerprint_config": fingerprint_cfg
#     }
#     try:
#         response = requests.post(url, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         print(response.status_code, data)
#         if data['code'] != "-1":
#             profile_id = data['data']['profile_id']
#             # profile_no = data['data']['profile_no']
#             return profile_id
#         return None
#     except Exception as e:
#         print(f"Error creating AdsPower profile: {e}")
#         return None
#
# def delete_adspower_profile(profile_id):
#     url = f"{ADSPOWER_HOST}/api/v2/browser-profile/delete"
#     payload = {
#         "profile_id": [profile_id]
#     }
#
#     response = requests.post(url,json=payload)
#     print(response.status_code, response.json())
#
# def open_adspower_browser(profile_id):
#     url = f"{ADSPOWER_HOST}/api/v2/browser-profile/start"
#
#     payload = {
#         "profile_id": profile_id,
#         "headless": "0",
#         "proxy_detection": "0",
#         "cdp_mask": "1",
#         "launch_args": [  # Ключевые аргументы Chrome
#             "--disable-blink-features=AutomationControlled",
#             "--disable-infobars",
#             "--disable-notifications",
#             "--disable-popup-blocking"
#         ],
#         "last_opened_tabs": "0",
#         "password_filling": "0",
#         "password_saving": "0"
#     }
#
#     response = requests.post(url, json=payload)
#     print(response.status_code)
#
#     data = response.json()
#     print(data)
#
#     debug_port = data['data']['debug_port']
#     if debug_port:
#         print(debug_port)
#         return debug_port
#     return None
#
# def check_adspower_browser_status(profile_id):
#     url = f"{ADSPOWER_HOST}/api/v2/browser-profile/active"
#     payload = {
#         "profile_id": profile_id
#     }
#
#     response = requests.get(url,json=payload)
#
#     print(response.status_code, response.json())
#
# def close_adspower_browser(profile_id):
#     url = f"{ADSPOWER_HOST}/api/v2/browser-profile/stop"
#     payload = {
#         "profile_id": profile_id
#     }
#
#     response = requests.get(url,json=payload)
#
#     print(response.status_code, response.json())
#
# def get_adspower_profile_cookies(profile_id):
#     url = f"{ADSPOWER_HOST}/api/v2/browser-profile/cookies"
#
#     payload = {
#         "profile_id": profile_id
#     }
#     response = requests.get(url, json=payload)
#     print(response.status_code)
#
#     data = response.json()
#
#     cookies = data['data']['cookies']
#     if cookies:
#         return cookies
#     return None
#
# API_2CAPTCHA = "ebdf9de880e9f0cc3759e3a016a3bd6c"
# SITEKEY = "6LcXfesZAAAAAJM2165Nf6nbqruGRJx8rdK6Bx3a"
# PAGE_URL = "https://es.wallapop.com/auth/signin?redirectUrl=%2F"
# EMAIL = "special.one90@hotmail.it"
# PASSWORD = "12345678qwert"
# WALLAPOP_LOGIN_URL = "https://es.wallapop.com/auth/signin=%2F"
# solver = TwoCaptcha(API_2CAPTCHA)
# def solve_wallapop_captcha():
#     """Решает reCAPTCHA Enterprise с помощью 2captcha и возвращает токен."""
#     try:
#         result = solver.recaptcha(
#             sitekey=SITEKEY,
#             url=PAGE_URL,
#             enterprise=1,  # Учитываем Enterprise
#         )
#         code = result.get("code")
#         print("✅ Капча решена (Enterprise v2), токен:", code)
#         return code
#     except Exception as e:
#         print(f"❌ Ошибка при решении капчи: {e}")
#         return None
#
# def wallapop_login_with_automated_captcha(profile_id):
#     """Автоматический вход на Wallapop с решением капчи через 2captcha."""
#     # Получаем debug port через ваш метод
#     debug_port = open_adspower_browser(profile_id)
#     if not debug_port:
#         print("❌ Не удалось получить debug port")
#         return
#
#     print(f"🛜 Получен debug port: {debug_port}")
#
#     # Получаем WebSocket URL через CDP
#     cdp_url = f"http://127.0.0.1:{debug_port}/json/version"
#     try:
#         response = requests.get(cdp_url)
#         response.raise_for_status()
#         cdp_data = response.json()
#         ws_url = cdp_data["webSocketDebuggerUrl"]
#         print(f"🔌 WebSocket URL: {ws_url}")
#     except Exception as e:
#         print(f"❌ Ошибка при получении WebSocket URL: {e}")
#         return
#
#     with sync_playwright() as p:
#         # Подключаемся к браузеру AdsPower через WebSocket
#         browser = p.chromium.connect_over_cdp(ws_url)
#         context = browser.contexts[0]
#         page = context.pages[0] if context.pages else context.new_page()
#         page.set_default_timeout(120000)
#
#         print("🌐 Открываю страницу входа Wallapop...")
#         page.goto("https://es.wallapop.com/auth/onboarding?redirectUrl=%2F")
#
#         # Принятие куки
#         try:
#             accept_button = page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
#             if accept_button:
#                 accept_button.click()
#                 print("🍪 Куки приняты!")
#                 time.sleep(1)
#         except:
#             print("⚠️ Куки уже приняты или элемент не найден")
#
#         # Кликаем на кнопку "Iniciar sesión"
#         login_button_selector = 'div.walla-button__children-container span:has-text("Iniciar sesión")'
#         page.click(login_button_selector)
#         print("✅ Кнопка 'Iniciar sesión' нажата")
#
#         # # Принятие куки
#         # try:
#         #     accept_button = page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
#         #     if accept_button:
#         #         accept_button.click()
#         #         print("🍪 Куки приняты!")
#         #         time.sleep(1)
#         # except:
#         #     print("⚠️ Куки уже приняты или элемент не найден")
#
#         # Ввод логина и пароля
#         try:
#             page.fill("#signin-email", EMAIL)
#             print("📧 Введен email")
#             page.fill("#signin-password", PASSWORD)
#             print("🔑 Введен пароль")
#         except Exception as e:
#             print(f"❌ Ошибка ввода логина/пароля: {e}")
#             browser.close()
#             return
#
#         # # Работа с капчей
#         # try:
#         #     print("🧩 Ожидаем появления капчи...")
#         #     captcha_frame = page.wait_for_selector('iframe[title*="reCAPTCHA"]', timeout=10000)
#         #     if captcha_frame:
#         #         frame = captcha_frame.content_frame()
#         #         checkbox = frame.wait_for_selector('.recaptcha-checkbox')
#         #         checkbox.click()
#         #         print("✅ Капча чекбокс нажат")
#         # except Exception as e:
#         #     print(f"⚠️ Ошибка при работе с капчей: {e}")
#
#         # time.sleep(5)
#         # Решение капчи и установка токена через JavaScript
#         print("🧩 Решаем капчу с помощью 2captcha...")
#         token = solve_wallapop_captcha()
#         print(token)
#         # token = page.evaluate('document.getElementById("recaptcha-token").value')
#         if not token:
#             print("❌ Не удалось получить токен капчи")
#             browser.close()
#             return
#
#         try:
#             js_code = f"""
#                 (function() {{
#                     const recaptchaResponse = document.getElementById('g-recaptcha-response');
#                     if (recaptchaResponse) {{
#                         recaptchaResponse.value = "{token}";
#                         const event = new Event('input', {{ bubbles: true }});
#                         recaptchaResponse.dispatchEvent(event);
#
#                         // Имитируем успешную валидацию reCAPTCHA
#                         if (typeof window.onRecaptchaSuccessCallback === 'function') {{
#                             window.onRecaptchaSuccessCallback("{token}");
#                         }}
#
#                         console.log("Токен reCAPTCHA установлен");
#                         return true;
#                     }}
#                     return false;
#                 }})();
#             """
#             result = page.evaluate(js_code)
#             if result:
#                 print("✅ Токен капчи установлен")
#             else:
#                 print("❌ Элемент reCAPTCHA не найден")
#
#             input("Любая клавиша ддля продолжения...")
#             # Нажатие кнопки входа
#             login_button = page.wait_for_selector('button[type="submit"]', timeout=5000)
#             if login_button:
#                 # Добавляем задержку перед кликом для имитации человеческого поведения
#                 time.sleep(random.uniform(0.5, 1.5))
#                 login_button.click()
#                 print("🔓 Кнопка входа нажата")
#
#                 # Ожидаем навигации
#                 page.wait_for_load_state("networkidle", timeout=30000)
#                 print("✅ Загрузка завершена")
#             else:
#                 print("❌ Кнопка входа не найдена")
#                 browser.close()
#                 return
#         except Exception as e:
#             print(f"❌ Ошибка при установке токена или входе: {e}")
#             browser.close()
#             return
#
#         # Проверка успешного входа
#         try:
#             # Ожидаем появления элемента профиля
#             page.wait_for_selector('a[data-testid="user-menu"]', timeout=15000)
#             print("✅ Вход выполнен успешно! Элемент профиля найден")
#
#             # Дополнительная проверка через URL
#             if "account" in page.url or "app" in page.url:
#                 print(f"✅ Подтверждение входа по URL: {page.url}")
#             else:
#                 print(f"⚠️ Необычный URL после входа: {page.url}")
#
#         except Exception as e:
#             print(f"❌ Ошибка при проверке входа: {e}")
#             # Проверяем наличие ошибок на странице
#             error_msg = page.query_selector('.error-message')
#             if error_msg:
#                 print(f"⚠️ Сообщение об ошибке: {error_msg.inner_text()}")
#
#             # Делаем скриншот для диагностики
#             page.screenshot(path="login_error.png")
#             print("📸 Скриншот ошибки сохранён как login_error.png")
#
#         # Получаем данные для дальнейшего использования
#         print("\n🔐 Получаем данные сессии для requests:")
#         cookies = context.cookies()
#         user_agent = page.evaluate("() => navigator.userAgent")
#
#         print(f"🍪 Куки: {len(cookies)} items")
#         print(f"🕶️ User-Agent: {user_agent[:50]}...")
#
#         # Создаем сессию requests
#         session = requests.Session()
#         session.headers.update({"User-Agent": user_agent})
#         for cookie in cookies:
#             session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
#
#         print("🛑 Отключаемся от браузера (браузер остается открытым)")
#         browser.disconnect()
#
#         return session  # Возвращаем готовую сессию
#
# def wallapop_login(profile_id):
#     # Получаем debug port
#     debug_port = open_adspower_browser(profile_id)
#     if not debug_port:
#         print("❌ Не удалось получить debug port")
#         return
#
#     print(f"🛜 Получен debug port: {debug_port}")
#
#     # Получаем WebSocket URL через CDP
#     cdp_url = f"http://127.0.0.1:{debug_port}/json/version"
#     try:
#         response = requests.get(cdp_url)
#         response.raise_for_status()
#         cdp_data = response.json()
#         ws_url = cdp_data["webSocketDebuggerUrl"]
#         print(f"🔌 WebSocket URL: {ws_url}")
#     except Exception as e:
#         print(f"❌ Ошибка при получении WebSocket URL: {e}")
#         return
#
#     with sync_playwright() as p:
#         # Подключаемся к браузеру AdsPower через WebSocket
#         browser = p.chromium.connect_over_cdp(ws_url)
#         context = browser.contexts[0]
#         page = context.pages[0] if context.pages else context.new_page()
#         page.set_default_timeout(120000)
#
#         print("🌐 Открываю страницу входа Wallapop...")
#         page.goto("https://es.wallapop.com/auth/onboarding?redirectUrl=%2F")
#
#         # Принятие куки
#         try:
#             accept_button = page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
#             if accept_button:
#                 accept_button.click()
#                 print("🍪 Куки приняты!")
#                 time.sleep(1)
#         except:
#             print("⚠️ Куки уже приняты или элемент не найден")
#
#         # Кликаем на кнопку "Iniciar sesión"
#         login_button_selector = 'div.walla-button__children-container span:has-text("Iniciar sesión")'
#         page.click(login_button_selector)
#         print("✅ Кнопка 'Iniciar sesión' нажата")
#
#         # Ввод email
#         try:
#             email_input = page.wait_for_selector('input#username', timeout=5000)
#             if email_input:
#                 email_input.fill(EMAIL)
#                 print("📧 Введен email")
#             else:
#                 print("❌ Поле для email не найдено")
#                 browser.close()
#                 return
#         except Exception as e:
#             print(f"❌ Ошибка ввода email: {e}")
#             browser.close()
#             return
#
#         # Ввод пароля
#         try:
#             password_input = page.wait_for_selector('input#password', timeout=5000)
#             if password_input:
#                 password_input.fill(PASSWORD)
#                 print("🔑 Введен пароль")
#             else:
#                 print("❌ Поле для пароля не найдено")
#                 browser.close()
#                 return
#         except Exception as e:
#             print(f"❌ Ошибка ввода пароля: {e}")
#             browser.close()
#             return
#
#         try:
#             # Нажатие кнопки входа
#             login_button = page.wait_for_selector(
#                 'button.walla-button__button--primary span:has-text("Acceder a Wallapop")', timeout=5000)
#             if login_button:
#                 # Добавляем задержку перед кликом для имитации человеческого поведения
#                 time.sleep(random.uniform(0.5, 1.5))
#                 login_button.click()
#                 print("🔓 Кнопка входа нажата")
#
#                 # Ожидаем навигации
#                 page.wait_for_load_state("networkidle", timeout=30000)
#                 print("✅ Загрузка завершена")
#             else:
#                 print("❌ Кнопка входа не найдена")
#                 browser.close()
#                 return
#
#         except Exception as e:
#             print(f"❌ Ошибка при входе: {e}")
#             browser.close()
#             return
#
#         browser.close()
#
#
#
# if  __name__ == "__main__":
#     profile = "k12pfh7c"
#
#
#     wallapop_login_with_automated_captcha(profile_id="k12qee0q")