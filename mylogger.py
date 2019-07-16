import logging


def getlogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch1 = logging.StreamHandler()
    ch2 = logging.FileHandler(r'logs/error_log.txt')
    ch1.setLevel(logging.DEBUG)
    ch2.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        '[%(asctime)s]'
        '[%(levelname)s]'
        '[pid=%(process)d]'
        '[thd=%(threadName)s]'
        '[%(module)s]'
        '%(message)s'
    )

    # add formatter to ch
    ch1.setFormatter(formatter)
    ch2.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch1)
    logger.addHandler(ch2)
    return logger


logger = getlogger()
