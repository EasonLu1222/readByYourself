import sys
import json
import time
import argparse
from instrument import PowerSensor
from mylogger import logger

PADDING = ' ' * 8


if __name__ == "__main__":
    logger.info(f'{PADDING}task_powersensor start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('channels_limits', help='channel', type=str)
    parser.add_argument('-p', '--ports',
                        help='serial com port for instruments', type=str)
    args = parser.parse_args()
    unpacked = json.loads(args.channels_limits)
    logger.info(f'{PADDING}unpacked: {unpacked}')
    channel_group = str(unpacked['args'][0])

    StartIndex=channel_group.find('[')
    Endindex=channel_group.find(']')
    Frequency=channel_group[StartIndex+2:Endindex-1]
    logger.info(f'{PADDING}Frequency: {Frequency}')

    #  limits = unpacked['limits']['null']
    limits = unpacked['limits'][Frequency]

    ports = json.loads(args.ports)
    logger.info(f'{PADDING}{ports}')
    visa_addr = ports['ks_powersensor'][0]
    logger.info(f'{PADDING}{visa_addr}')
    sn = visa_addr.split('::')[3]
    logger.info(f'{PADDING}{sn}')


    logger.info(f'{PADDING}limits: {limits}')

    p = PowerSensor(1, sn)

    logger.info(f'{PADDING}power sensor open')
    p.open()

    logger.info(f'{PADDING}power sensor init')
    p.init()

    logger.info(f'{PADDING}power sensor measure')
    ave_power = p.measure_power(Frequency)

    logger.info(f'{PADDING}ave_power: {ave_power}')

    logger.info(f'{PADDING}measure loop end')

    ifpass = ave_power > limits[0]
    result = [[f'Pass({ave_power})' if ifpass else f'Fail({ave_power})']]
    sys.stdout.write(json.dumps(result))
