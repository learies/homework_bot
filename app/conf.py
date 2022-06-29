import os

from dotenv import load_dotenv

load_dotenv()


REQUESTS_PERIOD = 10 * 60
ERROR_PERIOD = 29 * 60
API_URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

PRAKTIKUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
