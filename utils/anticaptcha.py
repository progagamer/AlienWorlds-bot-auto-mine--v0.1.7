import json


def acp_api_send_request(driver, message_type, data=None):
    """ Отправляет данные по url антикапчи, чтобы занести токен в расширение """

    if not data:
        data = {}

    message = {
        # всегда указывается именно этот получатель API сообщения
        'receiver': 'antiCaptchaPlugin',
        # тип запроса, например setOptions
        'type': message_type,
        # мерджим с дополнительными данными
        **data
    }
    # выполняем JS код на странице
    # а именно отправляем сообщение стандартным методом window.postMessage
    return driver.execute_script("return window.postMessage({});".format(json.dumps(message)))
