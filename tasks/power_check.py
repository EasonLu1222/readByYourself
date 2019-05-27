import sys
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('voltage', help='voltage', type=float)
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname
    voltage = args.voltage

    logging.info('power check start. [voltage: %s]' % voltage)
    import time; time.sleep(3)
    logging.info('power check end')

    if voltage == 3.3:
        logging.info('v = 3.3')
        sys.stdout.write(str(3.25))
    if voltage == 3.0:
        logging.info('v = 3')
        sys.stdout.write(str(2.8))
    if voltage == 5.0:
        logging.info('v = 5')
        sys.stdout.write(str(4.7))
    elif voltage == 19.0:
        logging.info('v = 19')
        sys.stdout.write(str(18))
