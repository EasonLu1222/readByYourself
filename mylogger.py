import logging


def getlogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    #  ch = logging.FileHandler(r'log.txt')
    ch.setLevel(logging.DEBUG)

    # create formatter
    #  formatter = logging.Formatter('[%(asctime)s][%(levelname)s][pid=%(process)d][thd=%(threadName)s][%(message)s]')
    formatter = logging.Formatter(
        '[%(asctime)s]'
        '[%(levelname)s]'
        '[pid=%(process)d]'
        '[thd=%(threadName)s]'
        '[%(module)s]'
        '%(message)s'
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


logger = getlogger()
