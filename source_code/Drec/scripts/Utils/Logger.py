import logging


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Logger(metaclass=SingletonMeta):
    def __init__(self):
        logging.basicConfig(filename='log.log', encoding='utf-8')
        self.logger = logging.getLogger('Drec: ')
        self.logger.setLevel('ERROR')
        self.log_idx = 0

    def log(self, message: str, level: str = 'DEBUG'):
        message = f'{self.log_idx}: {message}'
        if level.upper() == 'DEBUG':
            self.logger.debug(message)
        elif level.upper() == 'INFO':
            self.logger.info(message)
        elif level.upper() == 'WARNING':
            self.logger.warning(message)
        elif level.upper() == 'ERROR':
            self.logger.error(message)
        elif level.upper() == 'CRITICAL':
            self.logger.critical(message)
        self.log_idx += 1


if __name__ == '__main__':
    message = 'example message'
    Logger().log(message, 'DEBUG')
    Logger().log(message, 'INFO')
    Logger().log(message, 'WARNING')
    Logger().log(message, 'ERROR')
    Logger().log(message, 'CRITICAL')
