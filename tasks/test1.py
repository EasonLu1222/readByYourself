
import logging


logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


if __name__ == "__main__":
    logging.info('test1 start')
    import time; time.sleep(1.2)
    logging.info('test1 end')
