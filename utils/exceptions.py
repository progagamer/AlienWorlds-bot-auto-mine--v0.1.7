class CaptchaNotFound(Exception):
    """ Капча не найдена """

    pass


class ButtonNotFound(Exception):
    """ Кнопка не найдена """

    pass


class NotFound(Exception):
    """ Не найдено """

    pass


class MiningFail(Exception):
    """ Неудачный майнинг """

    pass


class LoginFailed(Exception):
    """ Неудачная авторизация """

    pass
