import re
from subprocess import Popen, PIPE


workdir = 'C:/LitePoint/IQfact_plus/IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng18_Lock/bin/'
exe = 'IQfactRun_Console.exe'
script1 = 'FIT_TEST_Sample_Flow.txt'
script2 = 'FIT_TEST_BT_Sample_Flow.txt'


def parse_testflow(f):
    lines = [e.rstrip() for e in f.readlines()]
    items = [e for e in lines if e.startswith('\t') and e.count('\t')==1]
    items = [e.strip() for e in items if not e.endswith('ALWAYS_SKIP')]
    return items


def run():
    process = Popen([f'{workdir}{exe}', '-RUN', f'{workdir}{script1}', '-exit'],
                 stdout=PIPE, cwd=workdir, shell=True)
    ended = False
    while True:
        line = process.stdout.readline()
        line = line.decode('utf8').rstrip()
        if 'In This Run' in line:
            ended = True
        if ended and not line:
            break
        yield line


def execute():
    print('execute start')
    process = Popen([f'{workdir}{exe}', '-RUN', f'{workdir}{script1}', '-exit'],
                 stdout=PIPE, cwd=workdir)
    print('process', process)
    outputs, _ = process.communicate()
    outputs = outputs.decode('utf8')
    lines = outputs.split('\n')
    for e in lines:
        print(e)


if __name__ == "__main__":
    print('main start')

    items = parse_testflow(open(f'{workdir}{script1}', 'r'))
    print('items', items)
    current_idx = 0
    processing_item = False
    #  pattern = '[\d]{1,4}\.[A-Z_]+  _____'
    pattern = '[\d]{1,4}\.%s' % items[current_idx]
    print(pattern)
    items_lines = []
    for line in run():
        print(line)
        matched = re.search(pattern, line)
        if matched:
            processing_item = True
            print('matched', matched)
            current_idx += 1
            if current_idx < len(items):
                pattern = '[\d]{1,4}\.%s' % items[current_idx]

        if processing_item:
            items_lines.append(line)

        if processing_item and line=='':
            if any(e for e in items_lines if 'Failed' in e):
                print(f'item {current_idx} {items[current_idx-1]} FAILED!!!')
            else:
                print(f'item {current_idx} {items[current_idx-1]} PASSED !!!')

            if current_idx == len(items):
                print('break')
                break
            
            items_lines = []
            processing_item = False

    print('main end')
