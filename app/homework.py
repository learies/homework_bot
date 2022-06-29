#!/usr/bin/env python3
import json
import logging
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram

from app.conf import (API_URL, CHAT_ID, ERROR_PERIOD, PRAKTIKUM_TOKEN,
                      REQUESTS_PERIOD, TELEGRAM_TOKEN)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

rotating_handler = RotatingFileHandler(
    'homework_bot.log', maxBytes=10 ** 7, backupCount=3
)

file_handler = logging.FileHandler('homework_bot.log', encoding='UTF-8')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)

logger.addHandler(rotating_handler)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

bot = telegram.Bot(token=TELEGRAM_TOKEN)

HOMEWORK_STATUSES = {
    'approved': 'Ревьюеру всё понравилось, работа зачтена!',
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'reviewing': 'Работа взята в ревью'
}


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def send_log_error(message):
    logger.error(message, exc_info=True)
    send_message(message)
    logger.info(
        f'Ошибка отправлена в чат: {CHAT_ID}\n'
        f'текст сообщения: {message}'
    )


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Отсутствует ключ "homework_name"')

    status = homework.get('status')
    if status is None:
        raise KeyError('Отсутствует ключ "status"')

    verdict = HOMEWORK_STATUSES.get(status)
    if verdict is None:
        raise ValueError(f'Получено неожиданное значение "status": "{status}"')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    try:
        homework_statuses = requests.get(
            url=API_URL,
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
            params={'from_date': current_timestamp}
        )

        statuse_code = homework_statuses.status_code
        if statuse_code != 200:
            desc = HTTPStatus(statuse_code).name
            raise ValueError(
                f'Некорректный ответ сервера: "{statuse_code}" ({desc})'
            )
        return homework_statuses.json()

    except requests.RequestException as re:
        message = f'Ошибка при отправке запроса. Ошибка {re}'
        send_log_error(message)

    except json.JSONDecodeError as je:
        message = f'Ошибка преобразования в JSON: {je}'
        send_log_error(message)
    return {}


def main():
    current_timestamp = int(time.time())
    while True:
        try:
            logger.debug('Program started')
            homeworks = get_homeworks(current_timestamp)

            current_date = homeworks.get('current_date')
            if current_date:
                current_timestamp = current_date

            homeworks = homeworks.get('homeworks')
            if homeworks is None:
                raise KeyError('Отсутствует ключ "homeworks"')

            for homework in homeworks:
                message = parse_homework_status(homework)
                send_message(message)
                logger.info(f'Статус отправлен в чат {CHAT_ID}')
            time.sleep(REQUESTS_PERIOD)

        except Exception as e:
            message = f'Бот упал с ошибкой: {e}'
            send_log_error(message)
            time.sleep(ERROR_PERIOD)


if __name__ == '__main__':
    main()
