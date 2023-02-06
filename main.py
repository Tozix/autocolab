import os
import traceback
from random import randint
from time import sleep

from dotenv import load_dotenv

import logger
from web import WebAction

load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
USER_DATA_DIR = os.getenv('USER_DATA_DIR')
APP_LOGGER_NAME = __name__
API_KEY = os.getenv('API_KEY')
UPLOAD_ENDPOINT = os.getenv('UPLOAD_ENDPOINT')
TRANSCRIPT_ENDPOINT = os.getenv('TRANSCRIPT_ENDPOINT')

log = logger.setup_applevel_logger(file_name='logs/main.log')


def main():
    web = WebAction(True)
    # Авторизуемся в гугле
    if not web.auth:
        web.google_auth(EMAIL, PASSWORD)
    log.debug('Авторизация пройдена успешно')
    while True:
        web.colab_run()
        wait_time = randint(60, 180)
        log.debug(f"Ожидаем перед повторным запуском: {wait_time} сек.")
        sleep(wait_time)


if __name__ == '__main__':
    try:
        log.info("Старт программы!")
        main()
    except Exception as error:
        message = f'Сбой в работе программы - [{error}]'
        log.critical(traceback.format_exc())
        log.error(message)
    except KeyboardInterrupt:
        print('Выход из программы')
        os._exit(1)
