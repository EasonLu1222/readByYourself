import sys
import json
import argparse
from instrument import DMM
from mylogger import logger

PADDING = ' ' * 8


def freq_in_range(channel, freq, limits):
    rng = limits[channel]
    #  if rng[0] < freq and freq < rng[2]: 
    if rng[0] < freq < rng[2]: 
        return 'Pass(%.3f)' % freq
    else:
        return 'Fail(%.3f)' % freq


if __name__ == "__main__":
    logger.info(f'{PADDING}speaker check...')
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

    logger.info(f'{PADDING}speaker check start. [channel_group: %s]' % channel_group)

    # for single channel read
    dmm = DMM(port=port_dmm, timeout=0.4)
    dmm.measure_volt(101)
    dmm.ser.close()

    # for multieple channels read
    dmm = DMM(port=port_dmm, timeout=5)

    logger.info(f'{PADDING}dmm.com: {dmm.com}')
    logger.info(f'{PADDING}dmm.is_open: {dmm.is_open}')
    logger.info(f'{PADDING}dmm.ser: {dmm.ser}')

    channels = sorted(sum(channel_group, []))
    logger.info(f'{PADDING}channels: {channels}')
    logger.info(f'{PADDING}type(channels): {type(channels)}')

    freqs = dmm.measure_freqs_all()
    chs = list(range(107, 109)) + list(range(115, 117))
    #  freqs_passfail = [freq_in_range(ch, e) for ch, e in zip(chs, freqs)]
    freqs_passfail = [freq_in_range(ch, e, limits) for ch, e in zip(channels, freqs)]

    logger.info(f'{PADDING}freqs: {freqs}')
    logger.info(f'{PADDING}passfail: {freqs_passfail}')

    
    channel_freq = dict(zip(channels, freqs_passfail))
    results = [[channel_freq[e] for e in g]for g in channel_group]

    sys.stdout.write(json.dumps(results))
