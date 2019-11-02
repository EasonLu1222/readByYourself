import os
import time
import logging
import pyclbr
import bisect
from logging.handlers import TimedRotatingFileHandler


class Module:
    def __init__(self, module):
        mod = pyclbr.readmodule_ex(module)
        line2func = []

        for classname, cls in mod.items():
            if isinstance(cls, pyclbr.Function):
                line2func.append((cls.lineno, "<no-class>", cls.name))
            else:
                for methodname, start in cls.methods.items():
                    line2func.append((start, classname, methodname))

        line2func.sort()
        keys = [item[0] for item in line2func]
        self.line2func = line2func
        self.keys = keys

    def line_to_class(self, lineno):
        index = bisect.bisect(self.keys, lineno) - 1
        return self.line2func[index][1]


def lookup_module(module):
    try:
        _module = Module(module)
    except AttributeError as ex:
        _module = None
    return _module


def lookup_class(module, funcname, lineno):
    if funcname == "<module>":
        return "<no-class>"

    try:
        module = lookup_module(module)
        className = module.line_to_class(lineno) if module else None
    except IndexError as ex:
        className = None
    return className



class MyLogFormatter(logging.Formatter):
    def format(self, record):
        record.className = lookup_class(
                record.module, record.funcName, record.lineno
        )
        if record.className:
            location = '%s.%s.%s' % (record.module, record.className, record.funcName)
            location = location.replace('<no-class>.', '')
        else:
            location = '%s.%s' % (record.module, record.funcName)

        msg = '%s %5s %5s %30s:%-4s %s' % (self.formatTime(record, '%m/%d %H:%M:%S'), record.levelname,
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
