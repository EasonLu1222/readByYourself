import sys
import json
import argparse
from instrument import DMM

from mylogger import logger


#  volt_ranges = {
    #  101: [18.05, 19.95],
    #  102: [4.75, 5.25],
    #  103: [3.135, 3.465],
    #  104: [1.282, 1.4175],
    #  105: [0.81, 1.09],
    #  106: [0.86, 1.14],
    #  109: [18.05, 19.95],
    #  110: [4.75, 5.25],
    #  111: [3.135, 3.465],
    #  112: [1.282, 1.4175],
    #  113: [0.81, 1.09],
    #  114: [0.86, 1.14],
#  }


def volt_in_range(channel, volt, limits):
    rng = limits[channel]
    if rng[0] < volt and volt < rng[2]: # min & max
        return 'Pass(%.3f)'% volt
    else:
        return 'Fail(%.3f)'% volt


if __name__ == "__main__":
    logger.info('power_check2 start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('channels_limits', help='channel', type=str)
    parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str)
    args = parser.parse_args()

    unpacked = json.loads(args.channels_limits)
    logger.info(f'unpacked: {unpacked}')
    channel_group = unpacked['args']
    limits = {int(k):v for k,v in unpacked['limits'].items()}

    port_dmm = args.port_dmm

    logger.info(f'channel_volt: {channel_group}')
    logger.info(f'limits: {limits}')

    # for single channel read
    dmm = DMM(port=port_dmm, timeout=0.4)
    dmm.measure_volt(101)
    dmm.ser.close()

    # for multieple channels read
    dmm = DMM(port=port_dmm, timeout=2)

    logger.info(f'dmm.com: {dmm.com}')
    logger.info(f'dmm.is_open: {dmm.is_open}')
    logger.info(f'dmm.ser: {dmm.ser}')

    channels = sorted(sum(channel_group, []))
    logger.info(f'channels: {channels}')
    logger.info(f'type(channels): {type(channels)}')

    # only for develop, virutal machine seems have some uart problem
    #  for ch in channels:
        #  volt = dmm.measure_volt(ch)
        #  logger.info(f'[{ch}] volt: {volt}')

    dmm.measure_volt(101)
    volts = dmm.measure_volts(channels)

    #  volts_passfail = [volt_in_range(ch,e) for ch, e in zip(channels, volts)]
    volts_passfail = [volt_in_range(ch, e, limits) for ch, e in zip(channels, volts)]
    logger.info(f'volts measured: {volts}')

    logger.info('power_check2 end...')

    channel_volt = dict(zip(channels, volts_passfail))

    results = [[channel_volt[e] for e in g]for g in channel_group]
    sys.stdout.write(json.dumps(results))
