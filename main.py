import os
import random
import time

import undetected_chromedriver as uc
from dotenv import load_dotenv
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
USER_DATA_DIR = os.getenv('USER_DATA_DIR')


class AutoColab:
    def __init__(self, email, password) -> None:
        self.email = email
        self.password = password
        options = uc.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1600,900")
        options.add_argument('--allow-profiles-outside-user-dir')
        # сбрасывает данные профиля в файл через n-ое число секунд.
        options.add_argument('--profiling-flush=10')
        # минимизирует потерю данных.
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument(f'--user-data-dir={USER_DATA_DIR}')
        options.add_argument(f'--profile-directory={EMAIL}')
        options.page_load_strategy = 'normal'
        self.driver = uc.Chrome(options=options)
        self.action = ActionChains(self.driver)

    @staticmethod
    def emu_key_press(string, el_obj):
        """Эмуляция постепенного ввода.
        Args:
            string (str): вводимые символы
            el_obj (obj): DOM obj
        """
        for s in string:
            time.sleep(random.uniform(0.1, 1.0))
            el_obj.send_keys(s)

    def click_to_el(self, el_obj):
        """Наведени, а потом клик по элементу.

        Args:
            el_obj: DOM объект
        """
        time.sleep(random.uniform(0.1, 1.0))
        self.action.click(el_obj).perform()

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

    def google_auth(self):
        """Аутификация в гугл аккаунте

        Args:
            email (str): мыло
            password (str): пароль
        """
        email_input = WebDriverWait(self.driver, timeout=3).until(
            lambda d: d.find_element(By.ID, "identifierId"))
        self.emu_key_press(self.email, email_input)

        nextButton = WebDriverWait(self.driver, timeout=3).until(
            lambda d: d.find_element(By.ID, "identifierNext"))
        self.click_to_el(nextButton)

        # div_password = driver.find_element(By.ID, 'password')
        # password_input = WebDriverWait(div_password, timeout=3).until(
        #    lambda d: d.find_element(By.TAG_NAME, "input"))
        # emu_key_press(password, password_input)

        # passwordNext = WebDriverWait(driver, timeout=5).until(
        #      lambda d: d.find_element(By.ID, "passwordNext"))
        # click_to_el(passwordNext)

    def colab_run(self):
        """Запуск скрипта колаба."""
        time.sleep(random.randint(10, 15))

        code_cell = self.driver.find_elements(
            By.CLASS_NAME, 'codecell-input-output')
        self.click_to_el(code_cell[0])

        time.sleep(random.randint(3, 10))
        self.action.key_down(Keys.CONTROL).key_down(
            Keys.ENTER).key_up(Keys.CONTROL).perform()

        buttons = self.driver.find_element(By.CLASS_NAME, 'buttons')
        apr = buttons.find_elements(By.TAG_NAME, 'paper-button')
        time.sleep(random.randint(5, 8))
        self.click_to_el(apr[1])
        time.sleep(random.randint(15, 40))

    def start(self):
        self.driver.get('https://google.ru')
        # Ищем ссылку(Элемент) на авторизацию
        link = self.search_el_atr_contains(
            'a', 'href', 'accounts.google.com/ServiceLogin')
        # Кликаем по элементу
        self.click_to_el(link)
        time.sleep(random.randint(5, 8))
        # Проверяем есть ли наш аккаунт в списке авторизации
        # chose_account = search_el_atr_contains('div', 'data-email', 'email')
        # if chose_account:
        #   print('Аккаунт уж был ранее авторизован')
        #   click_to_el(chose_account)
        # else:
        #   print('Ну тогда вводим пароль')

        # google_auth(email, password)


time.sleep(100)
