import os
import logging
import time
from logging.handlers import TimedRotatingFileHandler


def getlogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    log_dir = 'logs'
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # create console handler and set level to debug
    ch1 = logging.StreamHandler()
    ch2 = TimedRotatingFileHandler(f"{log_dir}/log.txt", when="H", interval=1, backupCount=48)

    ch1.setLevel(logging.DEBUG)
    ch2.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter(
        fmt='[%(asctime)s]'
        '[%(levelname)s]'
        '[%(module)s#%(lineno)d]'
        '%(message)s',
        datefmt='%m-%d %H:%M:%S'
    )

    # add formatter to ch
    ch1.setFormatter(formatter)
    ch2.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch1)
    logger.addHandler(ch2)
    return logger


logger = getlogger()
