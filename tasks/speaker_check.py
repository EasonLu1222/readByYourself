import sys
import json
import argparse
from instrument import DMM

from mylogger import logger


def freq_in_range(channel, freq, limits):
    #  rng = freq_ranges[channel]
    rng = limits[channel]
    if rng[0] < freq and freq < rng[2]: 
        return 'Pass(%.3f)' % freq
    else:
        return 'Fail(%.3f)' % freq


if __name__ == "__main__":
    logger.info('speaker check...')
    parser = argparse.ArgumentParser()
    #  parser.add_argument('channel', help='channel', type=str)
    parser.add_argument('channels_limits', help='channel', type=str)
    parser.add_argument('-pm',
                        '--port_dmm',
                        help='serial com port dmm',
                        type=str)
    args = parser.parse_args()

    #  channel_group = json.loads(args.channel)

    unpacked = json.loads(args.channels_limits)
    logger.info(f'unpacked: {unpacked}')
    channel_group = unpacked['args']
    limits = {int(k):v for k,v in unpacked['limits'].items()}
    
    port_dmm = args.port_dmm

    logger.info('speaker check start. [channel_group: %s]' % channel_group)

    # for single channel read
    dmm = DMM(port=port_dmm, timeout=0.4)
    dmm.measure_volt(101)
    dmm.ser.close()

    # for multieple channels read
    dmm = DMM(port=port_dmm, timeout=5)

    logger.info(f'dmm.com: {dmm.com}')
    logger.info(f'dmm.is_open: {dmm.is_open}')
    logger.info(f'dmm.ser: {dmm.ser}')

    channels = sorted(sum(channel_group, []))
    logger.info(f'channels: {channels}')
    logger.info(f'type(channels): {type(channels)}')

    freqs = dmm.measure_freqs_all()
    chs = list(range(107, 109)) + list(range(115, 117))
    #  freqs_passfail = [freq_in_range(ch, e) for ch, e in zip(chs, freqs)]
    freqs_passfail = [freq_in_range(ch, e, limits) for ch, e in zip(channels, freqs)]

    logger.info('...3')
    logger.info(f'freqs: {freqs}')
    logger.info(f'passfail: {freqs_passfail}')

    
    channel_freq = dict(zip(channels, freqs_passfail))
    results = [[channel_freq[e] for e in g]for g in channel_group]

    sys.stdout.write(json.dumps(results))
