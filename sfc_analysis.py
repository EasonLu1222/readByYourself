import os
import glob
from ftplib import FTP
import pandas as pd


pd.set_option('display.max_colwidth', 30)
pd.set_option('display.max_columns', 30)
pd.set_option('display.width', 1000)
pd.option_context('display.colheader_justify','right')


station = 'Audio'
stations_downloads = {
    'SA': 'downloads/SA',
    'RF': 'downloads/RF',
    'PowerSensor': 'downloads/PowerSensor',
}
stations_cols = {
    'SA': ['pid', 'result', 'failed', 't0', 't1', 'sta_id',
           'read_pid', 'load_led', 'led', 'unload_led', 'captouch', 'wifibt', 'ccode'],
    'PowerSensor': ['pid', 'result', 'failed', 't0', 't1', 'sta_id',
           'read_pid', '1n-a', '1n-b', '1ac-a', '1ac-b', '2n-a', '2n-b', '2ac-a', '2ac-b']
}


def combine(downloads_path, station):
    is_file_empty = lambda f: os.stat(f).st_size==0
    dd = []
    for file in sorted(glob.glob(f'{downloads_path}/*.csv')):
        print(file)
        if not is_file_empty(file):
            x = pd.read_csv(file)
            dd.append(x)
    df = pd.concat(dd)
    df = df[x.columns]
    df.columns = stations_cols[station]
    df.index = range(len(df))
    return df


def failed(df, col=None):
    col = col if col else 'result'
    ff = df[df[col].str.startswith('Fail')]
    return ff


def fails(df, col):
    #  df.loc[230,'failed'].split(',')
    return df.loc[col,'failed'].split(',')


if __name__ == "__main__":
    downloads_path = f'{stations_downloads[station]}'
    df = combine(downloads_path, station)
    f0 = failed(df)

    # for PowerSensor
    f1 =  failed(df, 'read_pid')
