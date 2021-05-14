import json
import logging
import time

from python_anticaptcha import NoCaptchaTaskProxylessTask
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver

import config
from utils.account import Account
from utils.exceptions import CaptchaNotFound, ButtonNotFound


class Control:
    def __init__(self, driver: webdriver.Firefox, index, game_account_name: str):
        """
        :param driver: Драйвер селениума
        :param index: Индекс потока
        :param game_account_name: Имя аккаунта
        """

        self.driver = driver
        self.index = index
        self.game_account_name = game_account_name

    def login(self):
        """ Авторизация в WAX кошельке """

        logging.info('Авторизация в WAX')

        self.driver.get('https://all-access.wax.io')
        with open(f'cookies/{self.index}.json', 'r') as f:
            for cookie in json.loads(f.read()):
                del cookie['sameSite']
                self.driver.add_cookie(cookie)

        self.driver.get(config.WORK_SITE_DIR)

        self.driver.execute_script('wax.login()')

        self.wait_windows_amount(2, '<')

        self.wait_page_load()

        self.click_approve_button()

        self.wait_windows_amount(1)

        self.change_window(0)

        time.sleep(5)

        user_account = Account.get_current_user_account(self.driver)

        self.game_account_name = user_account

        logging.info(f'Авторизация пройдена успешно ({user_account}).')

        return user_account

    def solve_captcha_by_extension(self):
        """ Решатель капчи. По факту дожидается пока расширение в браузере само решит капчу """

        self.wait_page_load()

        logging.info('Ожидаем решение капчи')

        # ждем ответа от решателя капчи в течении 120 сек
        try:
            WebDriverWait(self.driver, 90).until(lambda x: x.find_element_by_css_selector('.antigate_solver.solved'))
        except NoSuchElementException:
            raise CaptchaNotFound('Капча не найдена в течении 120 секунд. Рестарт.')

        logging.info('Капча решена')

    def solve_captcha_by_module(self, url: str, condition_for_finish=None):
        """
        Решатель капчи.

        :param url: URl сайта с капчей
        :param condition_for_finish: Условие для завершения поиска капчи

        :return captcha response: Токен который капча дает при решении
        """

        self.wait_page_load()

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        job = None
        while not job:
            captcha_not_found_count = 0

            site_key_el = None
            while not site_key_el:
                if condition_for_finish and condition_for_finish[0](*condition_for_finish[1]):
                    logging.info('Не надо решать капчу.')
                    return

                if captcha_not_found_count == 10:
                    raise CaptchaNotFound('Капча не найдена уже 10 раз. Рестарт.')

                try:
                    site_key_el = self.driver.find_element_by_xpath('//iframe[@title="reCAPTCHA"]')
                except NoSuchElementException:
                    self.switch_to_frame(par='title', arg='reCAPTCHA')

                    logging.warning('Капча не найдена. Еще одна попытка через 5 секунд.')

                    captcha_not_found_count += 1

                    site_key_el = None
                    time.sleep(5)

            site_key_el_src = site_key_el.get_attribute('src')
            site_key = site_key_el_src[site_key_el_src.find('&k=') + 3:site_key_el_src.find('&co')]

            logging.info('Ожидаем решения капчи.')

            task = NoCaptchaTaskProxylessTask(url, site_key)
            job = config.anticaptcha_client.createTask(task)
            job.join(90)
            if not job:
                logging.warning('Не удалось решить капчу за 120 сек. Еще одна попытка.')

        logging.info('Капча решена.')

        return job.get_solution_response()

    def change_window(self, window_index: int):
        """
        Изменить текущее окно (фокус)

        :param window_index: Индекс окна (игра - 0)
        """

        # если кол-во всех окон больше window_index
        if len(self.driver.window_handles) > window_index:
            window_after = self.driver.window_handles[window_index]  # новое окно
            self.driver.switch_to.window(window_after)  # переключаемся на новое окно

    def add_cookies_from_response_to_browser(self, response):
        """ Добавить куки из ответа (requests) в браузер """

        dict_resp_cookies = response.cookies.get_dict()
        response_cookies_browser = [{'name': name, 'value': value} for name, value in dict_resp_cookies.items()]
        for cookie in response_cookies_browser:
            self.driver.add_cookie(cookie)

    def add_cookies_from_browser_to_session(self, session):
        """ Добавить куки из браузера в сессию requests """

        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        return session

    def click_button(self, x: int, y: int, max_attempts: int = 30):
        """
        Нажатие на кнопку

        :param x: Координата кнопки по оси X
        :param y: Координата кнопки по оси Y
        :param max_attempts: Максимальное кол-во попыток. Если превысить - перезагрузка
        """

        fail_click_count = 0
        while fail_click_count < max_attempts:
            try:
                webdriver.ActionChains(self.driver).move_by_offset(x, y).click().perform()
                webdriver.ActionChains(self.driver).move_by_offset(-x, -y).perform()
                return
            except MoveTargetOutOfBoundsException:
                max_attempts += 1

                time.sleep(5)

        raise ButtonNotFound(f"Кнопка ({x}, {y}) не найдена за {max_attempts} попыток.")

    def wait_page_load(self):
        """ Дожидается загрузки страницы """

        while self.driver.execute_script('return document.readyState;') != 'complete':
            logging.info(f'Дожидаемся загрузки страницы {self.driver.current_url}.')

            time.sleep(5)

        logging.info(f'Страница ({self.driver.current_url}) загружена.')

    def switch_to_frame(self, par, arg):
        """
        Переключиться к фрейму

        :param par: Название параметра по которому искать фрейм, например title
        :param arg: Данные параметра
        """

        try:
            iframe = self.driver.find_element_by_xpath(f'//iframe[@{par}="{arg}"]')
        except NoSuchElementException:
            iframe = None
        if iframe:
            self.driver.switch_to.frame(iframe)
        else:
            logging.warning(f'FRAME "{par}={arg}" NOT FOUND')

    def click_approve_button(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        self.change_window(1)

        fail_click_button_count = 0
        while len(self.driver.window_handles) == 2:
            if fail_click_button_count == 10:
                raise ButtonNotFound("Кнопка APPROVE не найдена 10 раз. Рестарт.")

            time.sleep(10)

            self.wait_page_load()

            fail_click_button_count = 0
            approve_button = self.driver.find_element_by_xpath('//button[@class="button button-secondary button-large text-1-5rem text-bold mx-1"]')
            while True:
                if fail_click_button_count == 10:
                    raise ButtonNotFound("Кнопка APPROVE не найдена.")

                try:
                    approve_button.click()

                    break
                except ElementClickInterceptedException:
                    time.sleep(5)

                    self.driver.refresh()
                fail_click_button_count += 1

            time.sleep(6)
        self.change_window(0)

    def wait_windows_amount(self, amount: int, action: str = '!='):
        """
        Дожидается пока кол-во окон не будет = amount

        :param amount: Кол-во окон
        :param action: Тип проверки кол-ва окон
        """

        actions = {'==': len(self.driver.window_handles) == amount,
                   '!=': len(self.driver.window_handles) != amount,
                   '<=': len(self.driver.window_handles) <= amount,
                   '>=': len(self.driver.window_handles) >= amount,
                   '>': len(self.driver.window_handles) > amount,
                   '<': len(self.driver.window_handles) < amount}
        action = actions[action]

        while action:
            logging.info(f'Дожидаемся {amount} окна.')

            time.sleep(5)

        logging.info(f'{amount} окно найдено.')
