import random
from time import sleep

import undetected_chromedriver as uc
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

import logger

log = logger.get_logger(__name__)


class WebAction:
    def __init__(self, email, password, headless=True) -> None:
        self.email = email
        self.password = password
        options = uc.ChromeOptions()
        # Безголовый режим, еше не тестировал
        if headless:
            options.add_argument('--headless')
       # options.add_argument('--remote-debugging-port=9222')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1600,900")
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

    def click_to_el(self, el_obj):
        """Наведени, а потом клик по элементу.

        Args:
            el_obj: DOM объект
        """
        sleep(random.uniform(0.1, 1.0))
        self.action.click(el_obj).perform()

    def paper(self):
        paper_dialog = self.driver.find_element(By.TAG_NAME, 'paper-dialog')
        if paper_dialog:
            log.info("Появилось диалоговое окно")
            self.driver.get_screenshot_as_file('screenshots/paper-window.png')
            buttons = paper_dialog.find_elements(By.TAG_NAME, 'paper-button')
            if len(buttons) > 1:
                return buttons[1]
        return

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
        # Ожижание перед началом авторизации
        sleep(random.randint(1, 5))

        log.debug('Авторизация в ГУГЛ')
        # Скрин главной страницы
        self.driver.get_screenshot_as_file('screenshots/google_auth-start.png')

        # Ввод пароля
        email_input = self.driver.find_element(By.ID, "identifierId")
        self.emu_key_press(self.email, email_input)

        # Делаем скрин после ввода логина/email
        sleep(random.randint(1, 3))
        self.driver.get_screenshot_as_file('screenshots/google_auth-1.png')

        # Нажимаем на кнопку
        nextButton = self.driver.find_element(By.ID, "identifierNext")
        self.click_to_el(nextButton)

        # Делаем скрин окна ввода пароля
        sleep(random.randint(3, 6))
        self.driver.get_screenshot_as_file('screenshots/google_auth-2.png')

        # Ищем input поле и вводим пароль
        password_input = self.search_el_atr_contains(
            'input', 'type', 'password')
        # div_password = self.driver.find_element(By.ID, 'password')
        # password_input = div_password.find_element(By.TAG_NAME, "input")
        self.emu_key_press(self.password, password_input)
        # Делаем скрин после ввода пароля
        self.driver.get_screenshot_as_file(
            'screenshots/google_auth-password.png')

        # Ищем суббмит
        passwordNext = self.driver.find_element(By.ID, "passwordNext")
        # Пауза перед нажатием клавиши
        sleep(random.randint(1, 3))

        # Клик по клавише
        self.click_to_el(passwordNext)

        # Делаем скрин после авторизации
        sleep(random.randint(1, 3))
        self.driver.get_screenshot_as_file(
            'screenshots/google_auth-suc.png')
        log.debug("Прошли авторизацию")

    def colab_run(self):
        """Запуск скрипта колаба."""
        # Переходим на колаб
        log.info("Переходим на колаб в новой вкладке")
        self.driver.switch_to.new_window('tab')
        self.driver.get(
            'https://colab.research.google.com/drive/1u2dglBscyPswsUk-H2AHzDPOGTpB98RL?usp=sharing')
        self.colab_window = self.driver.current_window_handle

        # Ищем первую ячеку с кодом в блокноте
        sleep(random.randint(2, 8))
        code_cell = self.driver.find_elements(
            By.CLASS_NAME, 'codecell-input-output')
        log.info("Кликаем на первый блокнот")
        self.click_to_el(code_cell[0])

        sleep(random.randint(3, 5))
        # Жмем CTR+ENTER для запуска скрипта
        log.info("Нажимаем CTRL+ENTER")
        self.action.key_down(Keys.CONTROL).key_down(
            Keys.ENTER).key_up(Keys.CONTROL).perform()
        # Ждем окна подтверждения (Блокнот чужой)

        sleep(random.randint(3, 8))
        paper = self.paper()
        if paper is not None:
            log.info('Кликаем по бумаге')
            self.click_to_el(paper)
            sleep(random.randint(8, 15))

    def start(self):
        self.driver.get('https://google.ru')
        self.driver.get_screenshot_as_file('screenshots/main-page.png')
        # Сохраняем id вкладки
        self.original_window = self.driver.current_window_handle
        # Ожидание после загрузки страницы
        sleep(random.randint(3, 10))

        # Ищем ссылку(Элемент) на авторизацию
        link = self.search_el_atr_contains(
            'a', 'href', 'accounts.google.com/ServiceLogin')
        # Кликаем по элементу
        self.click_to_el(link)

        # Авторизация в гугл
        self.google_auth()

        # chose_account = self.search_el_atr_contains(
        #   'div', 'data-email', 'email')
        # if chose_account:
        #   log.info('Аккаунт есть в списке')
        #   self.click_to_el(chose_account)
        #  self.google_auth()
        # else:
        #    log.info('Аккаунт уж был ранее авторизован')
        # Открываем новую вкладку
        # self.colab_tab = self.driver.current_window_handle
        # Переключаемся на первую вкладку
        # self.driver.switch_to.window(self.original_window)

        # снова переключаемся на колаб
        # self.driver.switch_to.window(self.colab_tab)
        # Запускаем скрипт на колабе

        """
        while True:
            try:
                log.info("Запускаем колаб")
                self.colab_run()
            except Exception as e:
                log.error(f'Поймал исключение{e}')
            log.info('Закрываем вкладку')
            sleep(random.randint(60, 120))
            self.driver.get_screenshot_as_file('screenshots/b_close.png')
            self.driver.close()
            self.driver.get_screenshot_as_file('screenshots/d_close.png')
            sleep(random.randint(1, 3))
            driver.switch_to.window(self.original_window)
            sleep(random.randint(40, 90))
        """

    def capcha(self):
        self.driver.get('https://www.google.com/recaptcha/api2/demo')
        sleep(6000)
