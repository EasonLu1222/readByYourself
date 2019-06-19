import os
import sys
import json
import argparse

from mylogger import logger

def is_file_empty(fl):
    with open(fl, 'r') as f:
        content = f.read()
        return False if content else True

if __name__ == "__main__":
    logger.info('poweron start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('power_index', help='power_index', type=str)
    args = parser.parse_args()
    power_index = args.power_index

    logger.info(f'power_index: {power_index}')
    logger.info('\n\nAAAAA\n\n')
    while True:
        if os.path.isfile('power_results'):
            if not is_file_empty('power_results'):
                with open('power_results', 'r') as f:
                    x = json.load(f)
                    break
    logger.info('\n\nBBBBB\n\n')

    result = x[power_index]
    logger.info(f'result: {result}')

    os.remove('power_results')
    sys.stdout.write(f'Pass({result})')
