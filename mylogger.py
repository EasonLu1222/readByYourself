import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler


class MyLogFormatter(logging.Formatter):
    def format(self, record):
        location = '%s.%s' % (record.module, record.funcName)
        msg = '%s %5s %5s %25s:%-4s %s' % (self.formatTime(record, '%m/%d %H:%M:%S'), record.levelname,
                                          record.process, location, record.lineno, record.msg)
        record.msg = msg
        return super(MyLogFormatter, self).format(record)


def getlogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    log_dir = 'logs'
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # create console handler and set level to debug
    ch1 = logging.StreamHandler()
    ch2 = TimedRotatingFileHandler(f"{log_dir}/log.txt", when="H", interval=1, backupCount=48)

    ch1.setLevel(logging.DEBUG)
    ch2.setLevel(logging.DEBUG)
    # create formatter
    formatter = MyLogFormatter()

    # add formatter to ch
    ch1.setFormatter(formatter)
    ch2.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch1)
    logger.addHandler(ch2)
    return logger


logger = getlogger()
