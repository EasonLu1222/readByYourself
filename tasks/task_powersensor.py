import sys
import json
import time
import argparse
from instrument import PowerSensor

from mylogger import logger


if __name__ == "__main__":
    logger.info('task_powersensor start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('channels_limits', help='channel', type=str)
    parser.add_argument('-p', '--ports',
                        help='serial com port for instruments', type=str)
    args = parser.parse_args()
    unpacked = json.loads(args.channels_limits)
    logger.info(f'unpacked: {unpacked}')
    channel_group = str(unpacked['args'][0])

    StartIndex=channel_group.find('[')
    Endindex=channel_group.find(']')
    Frequency=channel_group[StartIndex+2:Endindex-1]
    logger.info(f'Frequency: {Frequency}')

    #  limits = unpacked['limits']['null']
    limits = unpacked['limits'][Frequency]

    ports = json.loads(args.ports)
    logger.info(ports)
    visa_addr = ports['ks_powersensor'][0]
    logger.info(visa_addr)
    sn = visa_addr.split('::')[3]
    logger.info(sn)


    logger.info(f'limits: {limits}')

    p = PowerSensor(1, sn)

    logger.info('power sensor open')
    p.open()

    logger.info('power sensor init')
    p.init()

    logger.info('power sensor measure')
    ave_power = p.measure_power(Frequency)

    logger.info(f'ave_power: {ave_power}')

    logger.info('measure loop end')

    ifpass = ave_power > limits[0]
    result = [[f'Pass({ave_power})' if ifpass else f'Fail({ave_power})']]
    sys.stdout.write(json.dumps(result))
