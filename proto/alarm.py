import time
import signal, os

to_quit = False

def handler(signum, frame):
    print('Signal handler called with signal', signum)
    with open('./xxx', 'a+') as f:
        f.write('abc')
    to_quit = True

    #  raise IOError("Couldn't open device!")

# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGINT, handler)

# This open() may hang indefinitely
#  fd = os.open('/dev/ttyS0', os.O_RDWR)

#  signal.alarm(0)          # Disable the alarm


if __name__ == "__main__":
    print('pid', os.getpid())
    while not to_quit:
        time.sleep(1)
