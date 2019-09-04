import sys
import json
import argparse
import pickle

from mylogger import logger
from utils import resource_path


if __name__ == "__main__":
    logger.info('poweron start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('power_index', help='power_index', type=int)
    args = parser.parse_args()
    power_index = args.power_index

    logger.info(f'power_index: {power_index}')

    with open(resource_path('instruments'), 'rb') as f:
        #  _, power1, power2 = pickle.load(f)
        power1, power2, _ = pickle.load(f)

    power = [power1, power2][power_index - 1]
    if not power.is_open:
        logger.info(f'open power{power_index}!')
        power.open_com()
        power.on()
        power.measure_current()

    result = power.max_current

    logger.info(f'result: {result}')
    sys.stdout.write(str(result))
