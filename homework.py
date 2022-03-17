import os
import time
import logging

import requests
import telegram
from http import HTTPStatus
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(
    'main.log',
    maxBytes=50000000,
    backupCount=2
)

formatter = logging.Formatter(
    '[%(asctime)s: %(levelname)s: %(lineno)d] %(message)s'
)

handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logger.info('удачная отправка сообщения в Telegram')
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """
    Делает запрос к эндпоинту API-сервиса.
    Возвращает ответ API, преобразовав его к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error(f'недоступность эндпоинта "{ENDPOINT}"')
        raise Exception('status_code отличный от 200')
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response['homeworks'], list):
        logger.error('ответ от API приходит не в виде списка')
        raise Exception('ответ от API приходит не в виде списка')

    if not response['homeworks']:
        logger.error('ответ от API содержит пустой словарь')
        raise Exception('ответ от API содержит пустой словарь')

    return response.get('homeworks')


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        logger.error('отсутствует ключ в словаре HOMEWORK_STATUSES')
        raise Exception('отсутствует ключ в словаре HOMEWORK_STATUSES')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('отсутствие обязательных переменных окружения')
        raise Exception("TOKEN не найден")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 2592000)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                send_message(bot, parse_status(homework[0]))
                current_timestamp = response.get('current_date')
                time.sleep(RETRY_TIME)
            logger.debug('отсутствие в ответе новых статусов')
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.error(f'сбой "{error}" при отправке сообщения в Telegram')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
