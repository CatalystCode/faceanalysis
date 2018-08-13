from logging import Formatter
from logging import Logger
from logging import StreamHandler
from logging import getLogger
from sys import stdout

from faceanalysis.settings import LOGGING_LEVEL


def get_logger(module_name: str) -> Logger:
    logger = getLogger(module_name)
    logger.setLevel(LOGGING_LEVEL)

    stream_handler = StreamHandler(stdout)
    stream_handler.setLevel(LOGGING_LEVEL)

    handler_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = Formatter(handler_format)
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger
