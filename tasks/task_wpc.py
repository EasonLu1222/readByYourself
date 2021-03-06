import sys
import json
import time
import argparse
from instrument import PowerSupply, Eloader
from mylogger import logger

PADDING = ' ' * 8


if __name__ == "__main__":
    logger.info(f'{PADDING}task_wpc start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('channels_limits', help='channel', type=str)
    parser.add_argument('-p', '--ports',
                        help='serial com port for instruments', type=str)
    args = parser.parse_args()

    unpacked = json.loads(args.channels_limits)
    logger.info(f'{PADDING}unpacked: {unpacked}')
    channel_group = unpacked['args']

    limits = unpacked['limits']['null']

    ports = json.loads(args.ports)
    logger.info(f'{PADDING}{ports}')

    logger.info(f'{PADDING}limits: {limits}')

    p = PowerSupply(1, ports['gw_powersupply'][0])
    e = Eloader(1, ports['gw_eloader'][0])

    p.init()
    e.init()

    p.start()
    e.start()

    logger.info(f'{PADDING}power idn: {p.gw_read_idn()}')
    logger.info(f'{PADDING}eloader idn: {e.gw_read_idn()}')

    i_in_list = []

    is_loading = lambda i_out: i_out>0
    def is_stable(i_in, i_in_list, i_in_tol=0.1):
        if len(i_in_list) > 1:
            return i_in - i_in_list[-1] < i_in_tol
        return False

    logger.info(f'{PADDING}measure loop start')
    while True:
        time.sleep(0.2)
        i_out = e.measure_current()
        if not i_out: continue
        elif not is_loading(i_out): continue
        v_in = p.measure_voltage()
        i_in = p.measure_cur()
        v_out = e.measure_voltage()
        i_in_list.append(i_in)
        if is_stable(i_in, i_in_list): break
    logger.info(f'{PADDING}measure loop end')
    logger.info(f'{PADDING}{i_in_list}')

    #p.off()
    e.stop()

    p_in = v_in * i_in
    p_out = v_out * i_out
    efficiency = (p_out / p_in)+0.01

    logger.info(f'{PADDING}v_in {v_in}')
    logger.info(f'{PADDING}i_in {i_in}')
    logger.info(f'{PADDING}v_out {v_out}')
    logger.info(f'{PADDING}i_out {i_out}')
    logger.info(f'{PADDING}p_in {p_in}')
    logger.info(f'{PADDING}p_out {p_out}')

    ifpass = efficiency > limits[0]
    result = [[f'Pass({efficiency})' if ifpass else f'Fail({efficiency})']]
    sys.stdout.write(json.dumps(result))
