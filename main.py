import os
import traceback

from dotenv import load_dotenv

import logger
from assai import AssemblyAI
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
    log.debug('Главная функция')
    capcha_text = AssemblyAI(API_KEY, TRANSCRIPT_ENDPOINT, UPLOAD_ENDPOINT)
    capcha_text.transcript('audio/audio.mp3')
    pass


if __name__ == '__main__':
    try:
        main()
        colab = WebAction(EMAIL, PASSWORD)
        log.info("Старт программы!")
        colab.start()
        # capcha_text = AssemblyAI()
        # capcha_text.transcript('audio.mp3')
    except Exception as error:
        message = f'Сбой в работе программы - [{error}]'
        log.critical(traceback.format_exc())
        log.error(message)
    except KeyboardInterrupt:
        # colab.driver.quit()
        print('Выход из программы')
        os._exit(1)
    finally:
        pass
        # colab.driver.quit()
