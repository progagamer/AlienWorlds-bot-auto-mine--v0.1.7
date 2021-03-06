import logging
import multiprocessing as mp
import os
import sys
import time

from utils.cookies import get_valid_cookies
from utils.game import Game

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s | %(processName)s')

logging.getLogger('seleniumwire.handler').setLevel(logging.WARNING)
logging.getLogger('seleniumwire.server').setLevel(logging.WARNING)


def main():
    try:
        accounts_names = []

        valid_cookies_index = get_valid_cookies(len(os.listdir('cookies')))
        for i in valid_cookies_index:
            logging.info(f'Запуск %s аккаунта', i)

            ctx = mp.get_context('spawn')
            queue = ctx.Queue()
            p = ctx.Process(target=Game().run, kwargs=dict(index=i, queue=queue))
            p.name = str(i)
            p.start()

            user_account = queue.get()

            logging.info('Аккаунт %s - %s', i, user_account)

            accounts_names.append(user_account)

        logging.info('Запуск аккаунтов окончен.')

        with open('WAXParser/accounts.txt', 'w') as f:
            for account in accounts_names:
                f.write(account + '\n')

        while True:
            time.sleep(5000)
    except KeyboardInterrupt:
        # завершение всех старых процессов мозиллы
        os.system('taskkill /f /im firefox.exe')

        logging.info("\nЗавершение работы бота...")
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.exit()


if __name__ == '__main__':
    # завершение всех старых процессов мозиллы
    os.system('taskkill /f /im firefox.exe')

    main()
# Claim TLM
def ClaimTLM():
    while True:
        delay_time = 300  # Wait 5 minutes then start new claim
