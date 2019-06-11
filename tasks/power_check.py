import sys
import logging
import argparse
from instrument import DMM

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


volt_ranges = {
    102: [4.75, 5.25],
    103: [3.135, 3.465],
    104: [1.71, 1.89],
    105: [1.282, 1.4175],
    106: [0.81, 1.09],
    107: [0.86, 1.14],
    108: [18.05, 19.95],
}


def volt_in_range(channel, volt):
    rng = volt_ranges[channel]
    if rng[0] < volt and volt < rng[1]:
        sys.stdout.write('Pass(%.3f)'% volt)
    else:
        sys.stdout.write('Fail(%.3f)'% volt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('channel', help='channel', type=float)
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str)
    args = parser.parse_args()
    portname = args.portname
    port_dmm = args.port_dmm
    channel = int(args.channel)

    logging.info('power check start. [channel: %s]' % channel)

    dmm = DMM(port=port_dmm, timeout=0.4)
    logging.info(f'dmm.com: {dmm.com}')
    logging.info(f'dmm.is_open: {dmm.is_open}')
    logging.info(f'dmm.ser: {dmm.ser}')

    if channel == 102:
        logging.info('channel: 102 --> 5V')
        volt = dmm.measure_volt(102)

    elif channel == 103:
        logging.info('channel: 103 --> 3.3V')
        volt = dmm.measure_volt(103)

    elif channel == 104:
        logging.info('channel: 104 --> 1.8V')
        volt = dmm.measure_volt(104)

    elif channel == 105:
        logging.info('channel: 105 --> 1.35V')
        volt = dmm.measure_volt(105)

    elif channel == 106:
        logging.info('channel: 106 --> 0.9V')
        volt = dmm.measure_volt(106)

    elif channel == 107:
        logging.info('channel: 107 --> 1.1V')
        volt = dmm.measure_volt(107)

    elif channel == 108:
        logging.info('channel: 108 --> 19V')
        volt = dmm.measure_volt(108)

    volt_in_range(channel, volt)
    logging.info(f'volt measured: {volt}')
    logging.info('power check end')
