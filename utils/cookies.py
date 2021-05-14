import json
import logging
import time

from selenium.common.exceptions import NoSuchElementException
from seleniumwire import webdriver

import config


def get_valid_cookies(cookies_amount):
    """
    Отобрать валидные куки из всех

    вводит wax.login(), если в открывшемся окне есть span class "warning-text", аккаунт не валиден
    """

    options = webdriver.FirefoxOptions()
    options.headless = True  # True - окно скрыто, False - окно не скрыто

    driver = webdriver.Firefox(options=options, executable_path='drivers/geckodriver.exe')

    valid_cookies_index = []

    for i in range(1, cookies_amount + 1):
        logging.info(f'Проверка %s куки', i)

        driver.delete_all_cookies()  # удаляем старые куки

        driver.get('https://all-access.wax.io')
        with open(f'cookies/{i}.json', 'r') as f:  # добавляем новые куки
            for cookie in json.loads(f.read()):
                del cookie['sameSite']
                driver.add_cookie(cookie)

        driver.get(config.WORK_SITE_DIR)

        try:
            driver.execute_script('wax.login()')
        except Exception as e:
            logging.info(f'Куки %s не прошел проверку. ({e.__str__()})', i)
            continue

        # дожидаемся 2 окна
        while len(driver.window_handles) < 2:
            time.sleep(1)

        # переключаемся на нужное окно
        for window in driver.window_handles:
            driver.switch_to.window(window)
            if driver.current_url == 'https://all-access.wax.io/cloud-wallet/login/':
                break

        while driver.execute_script('return document.readyState;') != 'complete':
            time.sleep(2)

        time.sleep(1)

        try:
            checked_element = driver.find_element_by_xpath('//span[@class="action-title"]')
        except NoSuchElementException:
            checked_element = None
        if checked_element and checked_element.text == 'You must login into WAX Cloud Wallet first':
            logging.info(f'Куки %s не прошел проверку.', i)
            continue

        # закрываем все старые окна
        for window in driver.window_handles[1:]:
            driver.switch_to.window(window)
            driver.close()

        driver.switch_to.window(driver.window_handles[0])  # переключаемся обратно на главное окно

        logging.info('Куки %s прошел проверку.', i)
        valid_cookies_index.append(i)

    logging.info('Проверка куки на валидность окончена.')

    driver.close()

    return valid_cookies_index
