# Abcproxy
import os
from dotenv import load_dotenv

load_dotenv()

PROXY_HOST = os.getenv('PROXY_HOST')
PROXY_PORT = int(os.getenv('PROXY_PORT'))
PROXY_ACCOUNT = os.getenv('PROXY_ACCOUNT')
PROXY_ZONE = os.getenv('PROXY_ZONE')
PROXY_PASS = os.getenv('PROXY_PASS')

def build_proxy(session: str) -> dict:  # Теперь принимает session
    proxy_user = f"{PROXY_ACCOUNT}-zone-{PROXY_ZONE}-session-{session}"
    proxy_url = f"socks5h://{proxy_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    return {
        "http": proxy_url,
        "https": proxy_url
    }

def build_adspower_proxy(session: str) -> dict:
    proxy_user = f"{PROXY_ACCOUNT}-zone-{PROXY_ZONE}-session-{session}"
    return {
        "proxy_soft": "other",
        "proxy_type": "socks5",
        "proxy_host": PROXY_HOST,
        "proxy_port": str(PROXY_PORT),
        "proxy_user": proxy_user,
        "proxy_password": PROXY_PASS,
        "global_config": "0"
    }


