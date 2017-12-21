import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def get_logger(module_name, log_file_name, logging_level):
    logging_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
    }
    logger = logging.getLogger(module_name)
    logger.setLevel(logging_levels[logging_level])

    dirname = os.path.dirname(os.path.abspath(__file__))
    logging_dir = os.path.join(dirname, 'logs')
    log_file = os.path.join(logging_dir, log_file_name)

    rotating_handler = RotatingFileHandler(log_file,
                                           maxBytes=1024**3,
                                           backupCount=2)
    rotating_handler.setLevel(logging_levels[logging_level])
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging_levels[logging_level])

    handler_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(handler_format)
    rotating_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    return logger
