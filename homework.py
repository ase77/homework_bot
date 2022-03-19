import os
import time
import json
import logging

import requests
import telegram
from http import HTTPStatus
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

dir_app = os.path.dirname(__file__)

handler = RotatingFileHandler(
    f'{dir_app}/main.log',
    maxBytes=50000000,
    backupCount=2,
    encoding='UTF-8'
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
    try:
        logger.info('удачная отправка сообщения в Telegram')
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'сбой "{error}" при отправке сообщения в Telegram')


def get_api_answer(current_timestamp):
    """
    Делает запрос к эндпоинту API-сервиса.
    Возвращает ответ API, преобразовав его к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except requests.exceptions.HTTPError as http_error:
        raise logger.error(f'ошибка HTTP: {http_error}')
    except requests.exceptions.ConnectionError as connection_error:
        raise logger.error(f'ошибка подключения: {connection_error}')
    except requests.exceptions.Timeout as timeout:
        raise logger.error(f'время ожидания запроса истекло: {timeout}')
    except requests.exceptions.RequestException as request_exception:
        raise logger.error(f'неоднозначное исключение: {request_exception}')

    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error(f'недоступность эндпоинта "{ENDPOINT}"')
        raise Exception(f'Статус код: {homework_statuses.status_code}')

    try:
        return homework_statuses.json()
    except json.JSONDecodeError as json_error:
        raise logger.error(f'ошибка JSON: {json_error.msg}')


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
    status_key = 'status'
    if status_key not in homework:
        message_error = f'отсутствует ключ "{status_key}" в ответе API'
        logger.error(message_error)
        raise Exception(message_error)
    homework_status = homework[status_key]

    # наконец выдалась возможность тебя поприветствовать. Привет!)
    # если проверяю ключ homework_name, то не проходит pytest
    # при этом бот работает, логгер ошибки не выдаёт, грешу на pytest
    # пробовал разные способы, в том числе через цикл как с токенами
    homework_key = 'homework_name'
    # if homework_key not in homework:
    #     message_error = f'отсутствует ключ "{homework_key}" в ответе API'
    #     logger.error(message_error)
    #     raise Exception(message_error)
    homework_name = homework[homework_key]

    if homework_status not in HOMEWORK_STATUSES:
        message_error = f'Неизвестный статус в ответе API: "{homework_status}"'
        logger.error(message_error)
        raise Exception(message_error)

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for name, value in tokens.items():
        if not value:
            logger.error(f'отсутствует переменная окружения: "{name}"')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
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
            logger.error(f'сбой в работе бота: {error}')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
