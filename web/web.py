import datetime
import os
import random
import traceback
import urllib
from time import sleep

import numpy as np
import scipy.interpolate as si
import undetected_chromedriver as uc
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import logger
from assai import AssemblyAI

USER_DATA_DIR = os.getenv('USER_DATA_DIR')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

load_dotenv()
log = logger.get_logger(__name__)

API_KEY = os.getenv('API_KEY')
UPLOAD_ENDPOINT = os.getenv('UPLOAD_ENDPOINT')
TRANSCRIPT_ENDPOINT = os.getenv('TRANSCRIPT_ENDPOINT')
USER_DATA_DIR = "chrome"
MIN_RAND = 0.64
MAX_RAND = 1.27
LONG_MIN_RAND = 4.78
LONG_MAX_RAND = 11.1
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


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
        options.add_argument("--window-size=1024,768")
        # Отключаем инфобары
        options.add_argument("--disable-infobars")
        # Работать в полноэранном режиме
        options.add_argument("start-maximized")
        # Отключить уведомления
        options.add_argument("--disable-notifications")
        options.add_experimental_option(
            "prefs", {"profile.default_content_setting_values.notifications": 1}
        )
        options.add_argument('--allow-profiles-outside-user-dir')
        # сбрасывает данные профиля в файл через n-ое число секунд.
        options.add_argument('--profiling-flush=10')
        # минимизирует потерю данных.
        options.add_argument('--enable-aggressive-domstorage-flushing')
        options.add_argument('--enable-profile-shortcut-manager')

        options.add_argument(
            '--user-data-dir=chrome')
        options.add_argument(f'--profile-directory={EMAIL}')

        # Ждать полной загрузки страницы
        options.page_load_strategy = 'normal'

        self.driver = uc.Chrome(driver_executable_path=f"{BASE_PATH}/chromedriver",
                                options=options)
        # Ожидание до получения элементов
        self.driver.implicitly_wait(10)
        self.action = ActionChains(self.driver)
        self.auth = False
        # Скоро не понадобится
        self.dom_type = {
            'TAG': By.TAG_NAME,
            'CLASS': By.CLASS_NAME,
            'ID': By.ID,
            'XPATH': By.XPATH
        }

    def waiting(self, a, b):
        """Пауза/Ожидание

        Args:
            a (float): ОТ
            b (float): И ДО в секундах
        """
        rand = random.uniform(a, b)
        log.debug(f"Ждем {rand} сек...")
        sleep(rand)

    def save_to_html(self, elem=None):
        """Сохраняем html элемента в файл.

        Args:
            elem (DOM object, optional): Dom объект.
             Если нет, то целиком текущую страницу.
        """
        now = str(datetime.datetime.today().strftime("%Y-%m-%d-%H%M%S"))
        if elem:
            with open(f"html/{now}_elem_page_source.html", "w", encoding='utf-8') as f:
                f.write(elem.get_attribute('innerHTML'))
        else:
            body = self.driver.find_element(By.TAG_NAME, "body")
            with open(f"html/{now}_full_page_source.html", "w", encoding='utf-8') as f:
                f.write(body.get_attribute('innerHTML'))

    def print_screen(self, action=""):
        """Делает скрин экрана.

        Args:
            action (str, optional): Описание скрина, пойдет в название файла "".
        """
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

    def search_el_atr_contains(self, tag, atr, contains, obj=None):
        """Перебор всех элементов по тэгу.
        проверка на соотвествие значению атрибута.

        Args:
            tag (str): httml тэг
            atr (str): имя атрибута
            contains (str): искомое значение атрибута

        Returns:
            Возращает DOM object если нашел
        """
        if not obj:
            obj = self.driver
        elements = obj.find_elements(By.TAG_NAME, tag)
        if elements:
            for idx, elem in enumerate(elements):
                if elem.get_attribute(atr) is not None:
                    if contains in elem.get_attribute(atr):
                        return elements[idx]
        return False

    def google_auth(self, email, password):
        """Авторизация в гугл аккаунте.
        Если работаем с профилями браузера, то нужна только при первом запуске.

        Args:
            email (str): мыло/логин
            password (str): пароль
        """
        self.email = email
        self.password = password
        self.driver.get('https://google.ru')

        # self.print_screen()
        # Сохраняем id вкладки
        self.original_window = self.driver.current_window_handle
        # Ожидание после загрузки страницы
        self.waiting(MIN_RAND, MAX_RAND)

        log.debug("Ищем кнопку на авторизацию")
        # Ищем ссылку(Элемент) на авторизацию
        link = self.search_el_atr_contains(
            'a', 'href', 'accounts.google.com/ServiceLogin')
        log.debug("Ищем ссылку на выход из аккаунта")
        sign_out_link = self.search_el_atr_contains(
            'a', 'href', 'accounts.google.com/SignOutOptions')
        if sign_out_link:
            self.print_screen('Session Exist!')
            log.debug("Юзер уже авторизован!")
            self.auth = True
            return

        self.print_screen()
        log.debug("Перемешаем курсор к кнопке войти")
        self.human_like_mouse_move(link)
        # Кликаем по элементу
        self.click_to(link)

        # Ожижание перед началом авторизации
        self.waiting(MIN_RAND, MAX_RAND)

        log.debug('Авторизация в ГУГЛ')
        # Скрин главной страницы
        # self.print_screen('Google main page')

        # Ввод логина/почты
        email_input = self.find_until_located(
            self.driver, By.ID, "identifierId")
        self.human_like_mouse_move(email_input)
        self.emu_key_press(self.email, email_input)

        # Делаем скрин после ввода логина/email
        self.waiting(MIN_RAND, MAX_RAND)
        # self.print_screen("After email typing")

        # Нажимаем на кнопку
        nextButton = self.find_until_located(
            self.driver, By.ID, "identifierNext")
        self.human_like_mouse_move(nextButton)
        self.click_to(nextButton)

        log.debug('Ищем Поле password')
        self.waiting(MIN_RAND, MAX_RAND)
        # self.print_screen("PASSWORD?")

        # password_obj = self.find_until_located(self.driver, By.ID, 'password')
        # Ищем input поле и вводим пароль
        # password_input = self.find_until_located(password_obj, By.TAG_NAME,'input')
        password_input = self.search_el_atr_contains(
            'input', 'autocomplete', 'password')
        self.human_like_mouse_move(password_input)
        self.click_to(password_input)
        # self.print_screen("BEFORE password typing")
        # div_password = self.driver.find_element(By.ID, 'password')
        # password_input = div_password.find_element(By.TAG_NAME, "input")
        self.emu_key_press(self.password, password_input)
        # Делаем скрин после ввода пароля
        # self.print_screen('after password')
        # self.print_screen("AFTER password typing")

        # Ищем сабмит
        passwordNext = self.find_until_located(
            self.driver, By.ID, "passwordNext")
        if passwordNext:
            log.debug('Нашел passwordNext')
        # self.save_to_html(passwordNext)
        # Пауза перед нажатием клавиши
        self.waiting(MIN_RAND, MAX_RAND)
        self.human_like_mouse_move(passwordNext)
        # Клик по клавише
        self.click_to(passwordNext)

        # Делаем скрин после авторизации
        self.waiting(MIN_RAND, MAX_RAND)
       # self.print_screen('after auth')
        self.auth = True

    def colab_run(self, notepad_url):
        """Запуск скрипта колаба."""
        # Разворачиваем экран
        # self.driver.maximize_window()

        # Переходим на колаб
        log.info("Переходим на колаб в новой вкладке")
        self.driver.switch_to.new_window('tab')
        self.driver.get(notepad_url)
        self.colab_window = self.driver.current_window_handle

        # Ищем первую ячеку с кодом в блокноте
        self.waiting(MIN_RAND, MAX_RAND)
        code_cell = self.driver.find_elements(
            By.CLASS_NAME, 'codecell-input-output')
        log.info("Кликаем на первый блокнот")
        self.click_to(code_cell[0])

        self.waiting(MIN_RAND, MAX_RAND)
        # Жмем CTR+ENTER для запуска скрипта
        log.info("Нажимаем CTRL+ENTER")
        self.action.key_down(Keys.CONTROL).key_down(
            Keys.ENTER).key_up(Keys.CONTROL).perform()

        count_dialog_check = 0
        while count_dialog_check < 3:
            count_dialog_check += 1
            self.waiting(MIN_RAND, MAX_RAND)
            if self.check_dialog():
                # Если появилось диалоговое окно, то сбрасываем счетчик
                count_dialog_check = 0
                self.paper_action()
        # self.print_screen("Colab running!")

        log.debug("Коллаб запущен!")
        # Закрываем вкладку с колабом
        self.driver.close()
        self.waiting(MIN_RAND, MAX_RAND)
        self.driver.switch_to.window(self.original_window)
        # self.print_screen("switch to main window")

    def human_like_mouse_move(self, start_element):
        points = [[6, 2], [3, 2], [0, 0], [0, 2]]
        points = np.array(points)
        x = points[:, 0]
        y = points[:, 1]

        t = range(len(points))
        ipl_t = np.linspace(0.0, len(points) - 1, 100)

        x_tup = si.splrep(t, x, k=1)
        y_tup = si.splrep(t, y, k=1)

        x_list = list(x_tup)
        xl = x.tolist()
        x_list[1] = xl + [0.0, 0.0, 0.0, 0.0]

        y_list = list(y_tup)
        yl = y.tolist()
        y_list[1] = yl + [0.0, 0.0, 0.0, 0.0]

        x_i = si.splev(ipl_t, x_list)
        y_i = si.splev(ipl_t, y_list)

        startElement = start_element

        self.action.move_to_element(startElement)
        self.action.perform()

        c = 5
        i = 0
        for mouse_x, mouse_y in zip(x_i, y_i):
            self.action.move_by_offset(mouse_x, mouse_y)
            self.action.perform()
            log.debug("Перемещаем курсор, %s ,%s" % (mouse_x, mouse_y))
            i += 1
            if i == c:
                break

    def solve_recaptcha(self):
        # Ищем фрейм с капчей
        self.waiting(MIN_RAND, MAX_RAND)
        iframe1 = self.search_el_atr_contains(
            'iframe', "src", "recaptcha/api2/anchor", self.colab_recaptcha_dialog)

        self.driver.switch_to.frame(iframe1)
        # Чекбокс капчи
        self.waiting(MIN_RAND, MAX_RAND)
        checkbox = self.find_until_clicklable(
            self.driver, By.ID, 'recaptcha-anchor')
        self.human_like_mouse_move(checkbox)
        log.debug('Клик по: recaptcha-anchor')
        self.click_to(checkbox)

        # self.waiting(MIN_RAND, MAX_RAND)
        # log.debug("Движение мышью")
        # self.human_like_mouse_move(checkbox)

        # Выходим из фрейма, на основную страницу
        self.driver.switch_to.default_content()
        # Это на случай, если google не распознал в нас бота
        try:
            self.driver.find_element(
                By.CLASS_NAME, 'recaptcha-checkbox-checked')
            log.debug('Нас не спалили, прошли тест Тьюринга!')
            return True
        except:
            pass

        log.debug("Ищем bframe")
        bframe = self.search_el_atr_contains(
            'iframe', "src", "recaptcha/api2/bframe", self.driver)
        if bframe:
            log.debug("Нашел bframe")
            log.debug("Меняем фрейм")
            self.driver.switch_to.frame(bframe)
        else:
            log.error('Фрейм с картинками не найден!')
            return

        self.waiting(MIN_RAND, MAX_RAND)
        log.debug('Ищем аудиокнопку')
        recaptcha_audio_button = self.find_until_located(
            self.driver, By.ID, 'recaptcha-audio-button')

        self.waiting(MIN_RAND, MAX_RAND)
        log.debug("Движение мышью")
        self.human_like_mouse_move(recaptcha_audio_button)
        log.debug('Клик по: recaptcha-audio-button')

        """
        Костыльный костыль, гугл начинает менять свойства элементов,
        а имено кнопки становятся то активными то нет в рандомном порядке,
        как гирлянда, можно поймать исключение при попытке кликнуть
        на устаревший элемент во время смены состояни!
        find_until_clicklable - дает кликать только на доступный элемент, но
        прямо во время клика может смениться состояние, по этому ниже
        обработаю исключение
        """
        while True:
            # find_until_clicklable - дает кликать только, на доступный к
            try:
                self.find_until_clicklable(
                    self.driver, By.ID, 'recaptcha-audio-button').click()
                log.debug("Клик прошел успешно!")
                break
            except:
                log.debug("Вам повезло и вы поймали исключение!")
        # Выходим из фрейма, на основную страницу
        self.driver.switch_to.default_content()
        log.debug("Ищем bframe")
        bframe = self.search_el_atr_contains(
            'iframe', "src", "recaptcha/api2/bframe", self.driver)
        if bframe:
            log.debug("Нашел bframe - audio")
            log.debug("Меняем фрейм - audio")
            self.driver.switch_to.frame(bframe)
        else:
            log.error('Фрейм аудио прослушать/скачать не найдено!')
            return
        # Ищем кнопку для прослушивания аудио
        play = self.find_until_clicklable(
            self.driver, By.CSS_SELECTOR, 'button.rc-button-default.goog-inline-block')
        download = self.find_until_located(
            self.driver, By.CSS_SELECTOR, 'a.rc-audiochallenge-tdownload-link')
        audio_response = self.find_until_located(
            self.driver, By.ID, 'audio-response')
        if play:
            log.debug('Нашли кнопочку play')
        if download:
            log.debug('Нашли сслыку скачать')
        if audio_response:
            log.debug('Нашли сслыку поле ответа')

        # Нажмем несколько раз кнопку воспроизвести, потом переместимся на поле ввода
        for _ in range(random.randint(0, 2)):
            self.waiting(MIN_RAND, MAX_RAND)
            self.human_like_mouse_move(play)
            log.debug('Клик по: play audio')
            self.click_to(play)
            self.waiting(3, 5)

        # Ткнем по ипуту, типа хочу ввести, то что просшулал
        self.waiting(MIN_RAND, MAX_RAND)
        self.human_like_mouse_move(audio_response)
        self.click_to(audio_response)
        log.debug('Клик по: audio_response')

        # Перемещаемся и скачиваем аудиофайл
        self.waiting(MIN_RAND, MAX_RAND)
        self.human_like_mouse_move(download)

        log.info('Скачиваем аудио')
        urllib.request.urlretrieve(
            download.get_attribute('href'), "audio/cap.mp3")
        ass = AssemblyAI(API_KEY, TRANSCRIPT_ENDPOINT, UPLOAD_ENDPOINT)
        text = ass.transcript("audio/cap.mp3")

        # Перемещаем на поле ввода
        self.human_like_mouse_move(audio_response)
        self.click_to(audio_response)
        self.emu_key_press(text, audio_response)
        # Ну и снова ждем
        self.waiting(MIN_RAND, MAX_RAND)

        recaptcha_verify_button = self.find_until_clicklable(self.driver, By.ID,
                                                             'recaptcha-verify-button')
        self.human_like_mouse_move(recaptcha_verify_button)
        self.click_to(recaptcha_verify_button)
        self.waiting(MIN_RAND, MAX_RAND)
        self.driver.switch_to.default_content()

        log.debug("Проверку прошел успешно")

    def gpu_limits(self):
        buttons = self.dialog_obj.find_elements(
            By.TAG_NAME, 'paper-button')
        if len(buttons) > 1:
            self.waiting(MIN_RAND, MAX_RAND)
            log.info("Соглашемся на работу без GPU")
            self.human_like_mouse_move(buttons[1])
            self.click_to(buttons[1])

    def paper_action(self):
        if self.dialog_type == "owner_dialog":
            buttons = self.dialog_obj.find_elements(
                By.TAG_NAME, 'paper-button')
            if len(buttons) > 1:
                self.waiting(MIN_RAND, MAX_RAND)
                log.info("Нажимаем по второй кнопке")
                self.human_like_mouse_move(buttons[1])
                self.click_to(buttons[1])
        elif self.dialog_type == "colab-recaptcha-dialog":
            log.debug('Запускаем решение рекапчи')
            self.solve_recaptcha()
        elif self.dialog_type == "limit_dialog":
            log.debug("Лимит на использование GPU исчерпан")
            self.gpu_limits()
        else:
            log.debug("Не описанное действие с окном, делаем скрин")
            # self.save_to_html(self.dialog_obj)
            self.print_screen("No action")

    def check_exists_element(self, find_by, cond, dom_obj=None):
        """_summary_

        Args:
            find_by (_type_): _description_
            cond (_type_): _description_
            dom_obj (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        if not dom_obj:
            dom_obj = self.driver
        try:
            page_obj = dom_obj.find_element(self.dom_type[find_by], cond)
        except NoSuchElementException:
            log.info(f"Не нашел элемент {cond} по {find_by}")
            return False
        return page_obj

    def check_dialog(self):
        """Проверка наличия диалоговых окон

        Returns:
            bool: Возращает True - если появились
        """
        log.info('Чекаем вспылвающие окна')

        if self.check_exists_element('TAG', 'colab-recaptcha-dialog'):
            log.debug('Окно: НАШЕЛ colab-recaptcha-dialog')
            self.dialog_type = "colab-recaptcha-dialog"
            self.colab_recaptcha_dialog = self.find_until_located(
                self.driver, By.TAG_NAME, 'colab-recaptcha-dialog')
            log.debug('Ну тип нашли значение')
            return True
        self.dialog_obj = self.check_exists_element('TAG', 'paper-dialog')
        if self.dialog_obj:
            if self.check_exists_element("TAG", 'b', self.dialog_obj):
                log.debug("Окно: Подтвердите запуск чужого блокнота")
                self.dialog_type = "owner_dialog"
                return True
            if self.search_el_atr_contains('a', 'href', 'colaboratory/faq.html#usage-limits', self.dialog_obj):
                log.debug(
                    "Окно: Невозможно подключиться к ускорителю (GPU) из-за лимитов на использование в Colab.")
                self.dialog_type = "limit_dialog"
                return True

        log.info("Диалоговых окон не нашел")
        self.dialog_type = None
        return False

    def find_until_located(self, driver, find_by, name, timeout=60):
        """Корректна проверка на наличие элемента на странице.

        Args:
            driver (driver): Драйвер браузера
            find_by (_type_): По какому элементу искать
            name (_type_): Имя искомого элемента/объекта
            timeout (int, optional): Таймаут, после после которого исключение вылетит.

        Returns:
            DOM obj: Найденый DOM
        """
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((find_by, name)))

    def find_until_clicklable(self, driver, find_by, name, timeout=60):
        """Корректно возвращает элементы доступные для клика.

        Args:
            driver (driver): Драйвер браузера
            find_by (_type_): По какому элементу искать
            name (_type_): Имя искомого элемента/объекта
            timeout (int, optional): Таймаут, после после которого исключение вылетит.

        Returns:
            DOM obj: Найденый DOM
        """
        return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((find_by, name)))

    def __del__(self):
        log.debug("Закрываем браузер при уничтожении объекта")
        # self.driver.quit()
