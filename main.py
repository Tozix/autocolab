import os
import traceback
from random import randint
from time import sleep

from dotenv import load_dotenv
from selenium.common.exceptions import (NoAlertPresentException,
                                        NoSuchWindowException,
                                        UnexpectedAlertPresentException)

import logger
from web import WebAction

load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
USER_DATA_DIR = os.getenv('USER_DATA_DIR')
APP_LOGGER_NAME = __name__
notepad_url = "https://colab.research.google.com/drive/1u2dglBscyPswsUk-H2AHzDPOGTpB98RL?usp=sharing"
log = logger.setup_applevel_logger(file_name='logs/main.log')


def main():
    web = WebAction()
    # Авторизуемся в гугле
    if not web.auth:
        web.google_auth(EMAIL, PASSWORD)
    log.debug('Авторизация пройдена успешно')
    for i in range(2):
        log.debug(f'Запуск № {i+1}')
        web.colab_run(notepad_url)
        wait_time = randint(60, 180)
        log.debug(f"Ожидаем перед повторным запуском: {wait_time} сек.")
        sleep(wait_time)
    log.debug('Перезапускаем драйвер и вот это вот все!')
    web.driver.quit()


if __name__ == '__main__':
    while True:
        try:
            log.info("Старт программы!")
            main()
        except UnexpectedAlertPresentException:
            log.error("Поймал алерт!")
        except NoAlertPresentException:
            log.error("Не смог подтвердить алерт!!")
        except NoSuchWindowException:
            log.error('Закрыто окно браузера')
        except Exception as error:
            message = f'Сбой в работе программы - [{error}]'
            log.critical(traceback.format_exc())
            log.error(message)
        except KeyboardInterrupt:
            print('Выход из программы')
            os._exit(1)
