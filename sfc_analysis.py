import os
import glob
from ftplib import FTP
import pandas as pd

pd.set_option('display.max_colwidth', 20)
pd.set_option('display.max_columns', 25)
pd.set_option('display.max_rows', 1000)
pd.set_option('display.width', 1000)
pd.option_context('display.colheader_justify', 'right')

stations_downloads = {
    'RF': 'downloads/RF',
    'Audio': 'downloads/Audio',
    'WPC': 'downloads/WPC',
    'SA': 'downloads/SA',
    'PowerSensor': 'downloads/PowerSensor',
}
stations_cols = {
    'RF': ['pid', 'result', 'failed', 't0', 't1', 'sta_id', 'read_pid'] +
    list(range(1, 59)),
    'Audio': [
        'pid', 'result', 'failed', 't0', 't1', 'sta_id',
        'read_pid', '2-apath', '3-frL', '4-thdL', '5-rfR', '6-thdR'
    ],
    'WPC': ['pid', 'result', 'failed', 't0', 't1', 'sta_id', 'eff'],
    'SA': [
        'pid', 'result', 'failed', 't0', 't1', 'sta_id', 'read_pid', 'load_led',
        'led', 'unload_led', 'fdr', 'captouch', 'wifibt', 'ccode'
    ],
    'PowerSensor': [
        'pid', 'result', 'failed', 't0', 't1', 'sta_id', 'read_pid', '1n-a',
        '1n-b', '1ac-a', '1ac-b', '2n-a', '2n-b', '2ac-a', '2ac-b'
    ]
}


def combine(downloads_path, station):
    is_file_empty = lambda f: os.stat(f).st_size == 0
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
    df = df.replace({'Pass': 'P', 'Fail': 'F'})
    df.failed = df.failed.fillna('')

    ff = df.failed.values.tolist()
    ff = [','.join([x[:x.find('(')] for x in e.split(',')]) for e in ff]
    df['failed'] = ff
    #  [e[:e.find('(')] for e in f.split(',')]
    #  xx = ','.join([e[:e.find('(')] for e in f.split(',')])

    return df


def failed(df, col=None, exclude_no_pid=True):
    col = col if col else 'result'
    ff = df[df[col].str.startswith('F')]
    if exclude_no_pid:
        ff = ff[ff.pid!='0']
    return ff


def summary(df, has_pid=True):
    dfd = df.drop_duplicates('pid')
    columns = dfd.columns.values.tolist()
    dfd = dfd.drop(['result', 't1'], axis=1)
    if has_pid:
        dfd = dfd.drop('read_pid', axis=1)
        columns.remove('read_pid')
    columns.remove('t1')

    lumped = pd.DataFrame(df.groupby('pid')['result'].sum())
    lumped = lumped.reset_index('pid')

    failed = df.groupby('pid').failed.agg(lambda x: '--'.join(x))

    s = pd.merge(dfd, lumped)[columns]

    # exclude no pid case
    result = s[s.pid!='0']
    return result


def fails(df, col):
    #  df.loc[230,'failed'].split(',')
    return df.loc[col, 'failed'].split(',')


if __name__ == "__main__":
    station = 'SA'
    downloads_path = f'{stations_downloads[station]}'
    df = combine(downloads_path, station)

    has_pid = station not in ['WPC']
    s = summary(df, has_pid=has_pid)
    if has_pid:
        # failed from no pid cases
        fr = failed(df, 'read_pid', exclude_no_pid=False)

    # failed summary
    fs = s[s.result.str.endswith('F')]

    # individual failed cases
    f0 = failed(df)
