import sys

from loguru import logger as loguru_logger


class Logger:
    def __init__(self):
        self._logger = loguru_logger
        try:
            self._logger.remove(0)
        except ValueError:
            self._logger.warning("Unable to remove previous logger")

        self._logger.add(sys.stdout,
                         colorize=True,
                         format="<level>{level}</level> {message}")

    def trace(self, message):
        self._logger.trace(message)

    def debug(self, message):
        self._logger.debug(message)

    def info(self, message):
        self._logger.info(message)

    def success(self, message):
        self._logger.success(message)

    def warning(self, message):
        self._logger.warning(message)

    def error(self, message):
        self._logger.error(message)

    def critical(self, message):
        self._logger.critical(message)


logger = Logger()
