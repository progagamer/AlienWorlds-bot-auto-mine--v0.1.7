import logging
import os
import time
from datetime import datetime

import pytz
import requests
from dateutil.tz import tzutc
from seleniumwire import webdriver

import config
from utils.control import Control
from .account import Account
from .anticaptcha import acp_api_send_request
from .exceptions import *
from .wax import Wax


class Game:
    def __init__(self):
        self.index = None
        self.game_account_name = None

        self.driver = None

        self.controller = None
        self.account = None
        self.wax = None

        self._run = True
        self._mining = True

        self.queue = None

    def init_driver(self, driver_path):
        seleniumwire_options = {}

        # _proxy = get_proxy()
        _proxy = None
        if _proxy:
            seleniumwire_options.update({'proxy': {
                'http': _proxy,
                'https': _proxy,
                'no_proxy': ''
            }})

        options = webdriver.FirefoxOptions()
        options.headless = config.headless  # True - окно скрыто, False - окно не скрыто

        self.driver = webdriver.Firefox(options=options, seleniumwire_options=seleniumwire_options, executable_path=driver_path)

        self.driver.set_window_position(0, 0)  # ставим окно в левый верхний угол
        self.driver.set_window_size(100, 300)  # устанавливаем фиксированный размер

        self.driver.install_addon(os.path.abspath('extensions/anticaptcha-plugin_v0.52.xpi'))  # устанавливаем плагин который решает капчу

        # вставляем ключ в решатель капчи
        self.driver.get('https://antcpt.com/blank.html')

        acp_api_send_request(self.driver, 'setOptions', {'options': {'antiCaptchaApiKey': config.CAPTCHA_KEY}})

    def run(self, index: int, queue, driver_path='drivers/geckodriver.exe'):
        """ Запуск игры """

        if not self.index:
            self.index = index
        if not self.queue:
            self.queue = queue
        if not self.driver:
            self.init_driver(driver_path)
        if not self.controller:
            self.controller = Control(self.driver, self.index, self.game_account_name)
        if not self.game_account_name:
            self.driver.get(config.WORK_SITE_DIR)

            user_account = None
            while not user_account:
                try:
                    user_account = self.controller.login()
                    self.account = Account(user_account)
                    self.controller = Control(self.driver, self.index, self.game_account_name)
                    self.game_account_name = user_account
                except Exception as e:
                    logging.info(f'Ошибка при запуске %s аккаунта: {e.__str__()}', self.index, exc_info=True)

            self.queue.put(user_account)
        if not self.wax:
            self.wax = Wax(self.driver, self.controller)

        self.controller.change_window(0)

        while self._mining:
            try:
                self.process_mine()
            except Exception as e:
                logging.error(f'{e.__str__()}. Рестарт через 10 секунд.')

                time.sleep(10)

                return self.restart()

    def go_to_work_site(self):
        self.driver.get(config.WORK_SITE_DIR)

    def restart(self):
        # закрываем все окна, кроме окна с игрой
        for i in range(1, len(self.driver.window_handles) - 1):
            self.controller.change_window(i)
            self.driver.close()

        self.controller.change_window(0)

        time.sleep(2.5)

        self.run(self.index, self.queue)

    def exit(self):
        """ Выход """

        logging.info('Выход...')

        self._run = False
        self._mining = False

        self.driver.quit()

    def process_mine(self):
     

        self.handle_account_ban()

      

    def handle_account_ban(self):
 

        logging.info(f'Начинаю майнинг.')

       
        logging.info(f'Проверка CPU.')
        tokens = requests.get(f'https://wax.eosrio.io/v2/state/get_tokens?account={self.game_account_name}').json()
        for token in tokens['tokens']:
            amount = format(token['amount'], '.4f')
            if token['symbol'] == 'TLM':
                if float(amount) > 0:
                    self.wax.send_tlm(self.game_account_name, config.MAIN_ACCOUNT, amount)
            elif token['symbol'] == 'WAX':
                if float(amount) > 0:
                    self.wax.send_wax(self.game_account_name, config.MAIN_ACCOUNT, amount)

       
        logging.info(f'Проверка успеха майнинга')
        assets = []
        for asset in self.account.get_user_assets().get('data', []):
            assets.append(int(asset['asset_id']))
        if assets:
            self.wax.send_nft(self.game_account_name, config.MAIN_ACCOUNT, assets)

        logging.info('Майнинг успешен. Жду следующего майна.')

        time.sleep(3600)

   