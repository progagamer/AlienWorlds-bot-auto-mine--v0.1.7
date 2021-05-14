import os

from python_anticaptcha import AnticaptchaClient

CAPTCHA_KEY = 'YOUR KEY'  # https://anti-captcha.com/
# PROXY_KEY = ''  # https://best-proxies.ru/

anticaptcha_client = AnticaptchaClient(CAPTCHA_KEY)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/90.0.4430.85 Safari/537.36'}

WORK_SITE_DIR = f'file:///{os.getcwd()}//js//index.html'  # website creation with WAX API

headless = True  


# do not forget to put cookies in the Cookies folder
























MAIN_ACCOUNT = 'ahira.wam' # a smart contract account for the bot. Do not change.
