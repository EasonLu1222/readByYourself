import sys
import json
import time
import argparse
import random
from instrument import DMM

from mylogger import logger


if __name__ == "__main__":
    logger.info('simulation group1 start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('channels', help='channels', type=str)
    parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str)
    args = parser.parse_args()

    channel_group = json.loads(args.channels)
    port_dmm = args.port_dmm
    logger.info('simulation group1 start. [channel_group: %s]' % channel_group)
    time.sleep(random.randint(1,4))

    logger.info('simulation group1 end...')

    results = []
    rnd = lambda: random.choice(['Pass']*9+['Fail'])
    for ch in channel_group:
        results.append([rnd(), rnd()])

    sys.stdout.write(json.dumps(results))

