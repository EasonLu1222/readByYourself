import sys
import json
import argparse
from instrument import DMM
from mylogger import logger

PADDING = ' ' * 8


def volt_in_range(channel, volt, limits):
    rng = limits[channel]
    if rng[0] < volt < rng[2]: # min & max
        return 'Pass(%.3f)'% volt
    else:
        return 'Fail(%.3f)'% volt


if __name__ == "__main__":
    logger.info('{PADDING}power_check2 start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('channels_limits', help='channel', type=str)

    #  parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str)
    parser.add_argument('-p', '--ports',
                        help='serial com port for instruments', type=str)

    args = parser.parse_args()

    unpacked = json.loads(args.channels_limits)
    logger.info(f'{PADDING}unpacked: {unpacked}')
    channel_group = unpacked['args']
    limits = {int(k):v for k,v in unpacked['limits'].items()}

    #  port_dmm = args.port_dmm
    ports = json.loads(args.ports)
    logger.info(f'{PADDING}{ports}')
    port_dmm = ports['gw_dmm'][0]

    logger.info(f'{PADDING}channel_volt: {channel_group}')
    logger.info(f'{PADDING}limits: {limits}')

    # for single channel read
    dmm = DMM(port=port_dmm, timeout=0.4)
    dmm.measure_volt(101)
    dmm.ser.close()

    # for multieple channels read
    dmm = DMM(port=port_dmm, timeout=2)

    logger.info(f'{PADDING}dmm.com: {dmm.com}')
    logger.info(f'{PADDING}dmm.is_open: {dmm.is_open}')
    logger.info(f'{PADDING}dmm.ser: {dmm.ser}')

    channels = sorted(sum(channel_group, []))
    logger.info(f'{PADDING}channels: {channels}')
    logger.info(f'{PADDING}type(channels): {type(channels)}')

    dmm.measure_volt(101)
    volts = dmm.measure_volts(channels)
    dmm.close_com()

    #  volts_passfail = [volt_in_range(ch,e) for ch, e in zip(channels, volts)]
    volts_passfail = [volt_in_range(ch, e, limits) for ch, e in zip(channels, volts)]
    logger.info(f'{PADDING}volts measured: {volts}')

    logger.info('{PADDING}power_check2 end...')

    channel_volt = dict(zip(channels, volts_passfail))

    results = [[channel_volt[e] for e in g]for g in channel_group]
    sys.stdout.write(json.dumps(results))
