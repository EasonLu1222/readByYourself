import sys
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


if __name__ == "__main__":
    voltage = sys.argv[1]

    logging.info('power check start. [voltage: %s]' % voltage)
    import time; time.sleep(2)
    logging.info('power check end')

    if voltage == '3.3':
        logging.info('v = 3.3')
        sys.stdout.write(str(3.25))
    if voltage == '3':
        logging.info('v = 3')
        sys.stdout.write(str(2.8))
    if voltage == '5':
        logging.info('v = 5')
        sys.stdout.write(str(4.7))
    elif voltage == '19':
        logging.info('v = 19')
        sys.stdout.write(str(18))
