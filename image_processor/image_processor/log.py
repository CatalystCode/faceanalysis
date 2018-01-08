import os
import sys
import logging

def get_logger(module_name, logging_level):
    logging_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
    }
    logger = logging.getLogger(module_name)
    logger.setLevel(logging_levels[logging_level])
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging_levels[logging_level])

    handler_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(handler_format)
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger
