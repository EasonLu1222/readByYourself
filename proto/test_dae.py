import time
from datetime import datetime


if __name__ == "__main__":
    while True:
        time.sleep(5)
        now = datetime.now()
        with open('C:\\Users\\zealz\\temp\\xxx', 'a+') as f:
            f.write(f'{now}\n')
