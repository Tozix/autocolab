import datetime
import os
import random
import traceback
import urllib
from time import sleep

import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import logger
from assai import AssemblyAI

log = logger.get_logger(__name__)


class WebAction:
    def __init__(self, headless=True) -> None:
        options = uc.ChromeOptions()
        # Безголовый режим, еше не тестировал
        if headless:
            options.add_argument('--headless')
            log.debug("Запущен безголовый режим")
        else:
            log.debug("Запущен режим с просмотром")
       # options.add_argument('--remote-debugging-port=9222')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1600,900")
        # Отключаем инфобары
        options.add_argument("--disable-infobars")
        # Работать в полноэранном режиме
        # options.add_argument("start-maximized")
        # Отключить уведомления
        options.add_argument("--disable-notifications")
        options.add_experimental_option(
            "prefs", {"profile.default_content_setting_values.notifications": 1}
        )
        # options.add_argument('--allow-profiles-outside-user-dir')
        # сбрасывает данные профиля в файл через n-ое число секунд.
        # options.add_argument('--profiling-flush=10')
        # минимизирует потерю данных.
        # options.add_argument('--enable-aggressive-domstorage-flushing')
        options.add_argument('--enable-profile-shortcut-manager')
        # options.add_argument(f'--user-data-dir={USER_DATA_DIR}')
        # options.add_argument(f'--profile-directory={EMAIL}')
        # Ждать полной загрузки страницы
        options.page_load_strategy = 'normal'
        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.action = ActionChains(self.driver)
        self.auth = False
        self.dom_type = {
            'TAG': By.TAG_NAME,
            'CLASS': By.CLASS_NAME,
            'ID': By.ID,
            'XPATH': By.XPATH
        }

    def save_to_html(self, elem=None):
        now = str(datetime.datetime.today().strftime("%Y-%m-%d-%H%M%S"))
        if elem:
            with open(f"html/{now}_elem_page_source.html", "w", encoding='utf-8') as f:
                f.write(elem.get_attribute('innerHTML'))
        else:
            body = self.driver.find_element(By.TAG_NAME, "body")
            with open(f"html/{now}_full_page_source.html", "w", encoding='utf-8') as f:
                f.write(body.get_attribute('innerHTML'))

    def print_screen(self, action=""):
        action = action.replace(" ", "_")
        now = str(datetime.datetime.today().strftime("%Y-%m-%d-%H%M%S"))
        stack = traceback.extract_stack()
        screen_name = f'{stack[-2][2]}-{action}{now}.png'
        self.driver.get_screenshot_as_file(f'screenshots/{screen_name}')
        log.info(f'Делаем скришот: {screen_name}')

    @staticmethod
    def emu_key_press(string, el_obj):
        """Эмуляция постепенного ввода.
        Args:
            string (str): вводимые символы
            el_obj (obj): DOM obj
        """
        for s in string:
            sleep(random.uniform(0.1, 1.0))
            el_obj.send_keys(s)

    def click_to(self, el_obj):
        """Наведени, а потом клик по элементу.

        Args:
            el_obj: DOM объект
        """
        sleep(random.uniform(0.1, 1.0))
        self.action.click(el_obj).perform()
        # После клика запускаем чекаем всплывающие окна
        # self.check_dialog()

    def search_el_atr_contains(self, tag, atr, contains):
        """Перебор всех элементов по тэгу.
        проверка на соотвествие значению атрибута.

        Args:
            tag (str): httml тэг
            atr (str): имя атрибута
            contains (str): искомое значение атрибута

        Returns:
            Возращает DOM object если нашел
        """
        elements = self.driver.find_elements(By.TAG_NAME, tag)
        if elements:
            for idx, elem in enumerate(elements):
                if elem.get_attribute(atr) is not None:
                    if contains in elem.get_attribute(atr):
                        return elements[idx]
        return

    def google_auth(self, email, password):
        self.email = email
        self.password = password
        self.driver.get('https://google.ru')

        self.print_screen()
        # Сохраняем id вкладки
        self.original_window = self.driver.current_window_handle
        # Ожидание после загрузки страницы
        sleep(random.uniform(0.5, 5.0))

        # Ищем ссылку(Элемент) на авторизацию
        link = self.search_el_atr_contains(
            'a', 'href', 'accounts.google.com/ServiceLogin')
        # Кликаем по элементу
        self.click_to(link)
        """Аутификация в гугл аккаунте

        Args:
            email (str): мыло
            password (str): пароль
        """
        # Ожижание перед началом авторизации
        sleep(random.uniform(0.5, 3.0))

        log.debug('Авторизация в ГУГЛ')
        # Скрин главной страницы
        self.print_screen()

        # Ввод пароля
        email_input = self.driver.find_element(By.ID, "identifierId")
        self.emu_key_press(self.email, email_input)

        # Делаем скрин после ввода логина/email
        sleep(random.uniform(0.5, 3.0))
        # self.print_screen()

        # Нажимаем на кнопку
        nextButton = self.driver.find_element(By.ID, "identifierNext")
        self.click_to(nextButton)

        sleep(random.uniform(1.0, 3.0))

        # Ищем input поле и вводим пароль
        password_input = self.search_el_atr_contains(
            'input', 'type', 'password')
        # div_password = self.driver.find_element(By.ID, 'password')
        # password_input = div_password.find_element(By.TAG_NAME, "input")
        self.emu_key_press(self.password, password_input)
        # Делаем скрин после ввода пароля
        # self.print_screen('after password')

        # Ищем суббмит
        passwordNext = self.driver.find_element(By.ID, "passwordNext")
        # self.save_to_html(passwordNext)
        # Пауза перед нажатием клавиши
        sleep(random.uniform(1.0, 3.0))

        # Клик по клавише
        self.click_to(passwordNext)

        # Делаем скрин после авторизации
        sleep(random.uniform(1.0, 3.0))
        # self.print_screen('after auth')
        self.auth = True

    def colab_run(self):
        # Разворачиваем экран
        self.driver.maximize_window()
        """Запуск скрипта колаба."""
        # Переходим на колаб
        log.info("Переходим на колаб в новой вкладке")
        self.driver.switch_to.new_window('tab')
        self.driver.get(
            'https://colab.research.google.com/drive/1u2dglBscyPswsUk-H2AHzDPOGTpB98RL?usp=sharing')
        self.colab_window = self.driver.current_window_handle

        # Ищем первую ячеку с кодом в блокноте
        sleep(random.uniform(1.5, 6.0))
        code_cell = self.driver.find_elements(
            By.CLASS_NAME, 'codecell-input-output')
        log.info("Кликаем на первый блокнот")
        self.click_to(code_cell[0])

        sleep(random.uniform(1.5, 8.0))
        # Жмем CTR+ENTER для запуска скрипта
        log.info("Нажимаем CTRL+ENTER")
        self.action.key_down(Keys.CONTROL).key_down(
            Keys.ENTER).key_up(Keys.CONTROL).perform()

        i = 0
        while i < 3:
            i += 1
            sleep(random.randint(1, 3))
            if self.check_dialog():
                self.paper_action()

        # self.print_screen("Colab running!")

        log.debug("Коллаб запущен!")
        # Закрываем вкладку с колабом
        self.driver.close()
        sleep(random.uniform(0.5, 1.1))
        self.driver.switch_to.window(self.original_window)
        # self.print_screen("switch to main window")

    def solve_recaptcha(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        sleep(random.uniform(0.3, 5.0))
        dialog = self.check_exists_element(
            'TAG', 'colab-recaptcha-dialog')
        iframe1 = self.check_exists_element(
            'TAG', 'iframe', dialog)
        self.save_to_html(iframe1)
        self.driver.switch_to.frame(iframe1)

        sleep(random.uniform(0.3, 5.0))

        checkbox_border = self.check_exists_element(
            'CLASS', 'recaptcha-checkbox-border')
        if checkbox_border:
            log.debug('Клик по: recaptcha-checkbox-border')
            self.click_to(checkbox_border)
            self.driver.switch_to.default_content()
        else:
            return

        sleep(random.uniform(0.3, 5.0))
        checked = self.check_exists_element(
            'CLASS', 'recaptcha-checkbox-checked')
        if not checked:
            dialog = self.check_exists_element(
                'TAG', 'colab-recaptcha-dialog')
            if not dialog:
                log.debug('Капча успешно решена!')
                return

        sleep(random.uniform(0.3, 5.0))
        iframe2 = self.check_exists_element(
            'XPATH', '//*[@title="текущую проверку reCAPTCHA можно пройти в течение ещё двух минут"]')
        self.save_to_html(iframe2)
        self.driver.switch_to.frame(iframe2)

        recaptcha_audio_button = self.check_exists_element(
            'ID', 'recaptcha-audio-button')
        if recaptcha_audio_button:
            log.debug('Клик по: recaptcha-audio-button')
            self.click_to(recaptcha_audio_button)
            self.driver.switch_to.default_content()
        else:
            sleep(600)
            return

        sleep(random.uniform(0.3, 5.0))
        header_text = self.check_exists_element(
            'CLASS', 'rc-doscaptcha-header-text')
        if header_text:
            self.driver.switch_to.default_content()
            log.error(f'Походе гугл заблокировал прохождение капчи')

        log.info(f'Решение капчи капчи...')
        tdownload_link = self.check_exists_element(
            'CLASS', 'rc-audiochallenge-tdownload-link')
        if tdownload_link:
            audio_url = tdownload_link.get_attribute('href')
            log.debug(f'URL аудио: {audio_url}')
        else:
            return
        log.info('Скачиваем аудио')
        urllib.request.urlretrieve(audio_url, "audio/cap.mp3")
        ass = AssemblyAI()
        text = ass.transcript("audio/cap.mp3")

        audio_response = self.check_exists_element(
            'ID', 'audio-response')
        if not audio_response:
            return

        self.emu_key_press(text, audio_response)
        sleep(random.uniform(0.3, 5.0))

        recaptcha_verify_button = self.check_exists_element(
            'ID', 'recaptcha-verify-button')
        if recaptcha_verify_button:
            log.debug('recaptcha-verify-button')
            self.click_to(recaptcha_verify_button)
            self.driver.switch_to.default_content()
        else:
            return

        sleep(random.uniform(0.3, 5.0))
        msg = self.check_exists_element(
            'CLASS', 'rc-audiochallenge-error-message').text
        if msg != '':
            self.driver.switch_to.default_content()
            log.error(f'Капча не решена: {str(msg)}')
        else:
            log.info('Капча решена')
            self.driver.switch_to.default_content()

        os.remove("audio/cap.mp3")

    def paper_action(self):
        if self.dialog_type == "owner_dialog":
            buttons = self.dialog_obj.find_elements(
                By.TAG_NAME, 'paper-button')
            if len(buttons) > 1:
                sleep(random.randint(3, 8))
                log.info("Нажимаем по второй кнопке")
                self.click_to(buttons[1])
        elif self.dialog_type == "colab-recaptcha-dialog":
            log.debug('Запускаем решение рекапчи')
            self.solve_recaptcha()
        else:
            log.debug("Не описанное действие с окном, делаем скрин")
            self.save_to_html(self.dialog_obj)
            self.print_screen("No action")

    def check_exists_element(self, by, cond, dom_obj=None):
        if not dom_obj:
            dom_obj = self.driver
        try:
            page_obj = dom_obj.find_element(self.dom_type[by], cond)
        except NoSuchElementException:
            log.info(f"Не нашел элемент {cond} по {by}")
            return False
        return page_obj

    def check_dialog(self):
        log.info('Чекаем вспылвающе окна')

        if self.check_exists_element('TAG', 'colab-recaptcha-dialog'):
            log.debug('Окно: НАШЕЛ colab-recaptcha-dialog')
            self.dialog_type = "colab-recaptcha-dialog"
            return True

        if self.check_exists_element('TAG', 'paper-dialog'):
            self.dialog_obj = self.check_exists_element('TAG', 'paper-dialog')
            if self.check_exists_element("TAG", 'b', self.dialog_obj):
                log.debug("Окно: Подтвердите запуск чужого блокнота")
                self.dialog_type = "owner_dialog"
                return True

        log.info("Диалоговых окон не нашел")
        self.dialog_obj = None
        self.dialog_type = None
        return False

    def __del__(self):
        log.debug("Закрываем браузер при уничтожении объекта")
        self.driver.quit()
