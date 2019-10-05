import os
import logging
from logging.handlers import TimedRotatingFileHandler
import zipfile
import codecs
import time
import glob


class TimedCompressedRotatingFileHandler(TimedRotatingFileHandler):
    def doRollover(self):
        self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if os.path.exists(dfn):
            os.remove(dfn)
        os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            # find the oldest log file and delete it
            s = glob.glob(self.baseFilename + ".20*")
            if len(s) > self.backupCount:
                s.sort()
                os.remove(s[0])
        if self.encoding:
            self.stream = codecs.open(self.baseFilename, 'w', self.encoding)
        else:
            self.stream = open(self.baseFilename, 'w')
        self.rolloverAt = self.rolloverAt + self.interval
        if os.path.exists(dfn + ".zip"):
            os.remove(dfn + ".zip")
        file = zipfile.ZipFile(dfn + ".zip", "w")
        file.write(dfn, os.path.basename(dfn), zipfile.ZIP_DEFLATED)
        file.close()
        os.remove(dfn)


def getlogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    log_dir = 'logs'
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # create console handler and set level to debug
    ch1 = logging.StreamHandler()
    ch2 = TimedCompressedRotatingFileHandler(f"{log_dir}/log.txt", when="H", interval=1, backupCount=48)
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
