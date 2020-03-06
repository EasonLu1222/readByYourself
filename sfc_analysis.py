import os
import glob
from ftplib import FTP
import pandas as pd

pd.set_option('display.max_colwidth', 30)
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
stations_col_drop = {
    'RF': [],
    'Audio': [],
    'WPC': [],
    'SA': ['t1', 'load_led', 'led', 'unload_led', 'fdr', 'captouch'],
    'PowerSensor': [],
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



class FailureAnalysis():
    def __init__(self, df, station):
        self.station = station
        self.df = df

    def failed(self, col=None, exclude_no_pid=True):
        col = col if col else 'result'
        ff = self.df[self.df[col].str.startswith('F')]
        if exclude_no_pid:
            ff = ff[ff.pid!='0']
        fff = ff.drop(columns=stations_col_drop[self.station])
        return fff

    def summary(self):
        dfd = self.df.drop_duplicates('pid')
        columns = dfd.columns.values.tolist()
        dfd = dfd.drop(['result', 't1'], axis=1)
        columns.remove('t1')
        lumped = pd.DataFrame(self.df.groupby('pid')['result'].sum())
        lumped = lumped.reset_index('pid')
        s = pd.merge(dfd, lumped)[columns]
        # exclude no pid case
        result = s[s.pid!='0']
        return result


def sa_fa():
    station = 'SA'
    downloads_path = f'{stations_downloads[station]}'
    df = combine(downloads_path, station)

    # 分析read_pid failed項目
    f_readpid = failed(df, 'read_pid', exclude_no_pid=False)

    # 分析mac wifibt failed項目
    f_macaddr = failed(df, 'wifibt', exclude_no_pid=False)

    # failed summary
    f_summary = summary(df)
    fs = f_summary[f_summary.result.str.endswith('F')]

    # individual failed cases
    f0 = failed(df)

    return f_summary, fs, f0, f_readpid, f_macaddr


def SA_FA(sa):
    sa.df.fdr = sa.df.fdr.fillna('')
    sa.df.wifibt = sa.df.wifibt.fillna('Fail(NaN)')

    # 分析read_pid failed項目
    f_readpid = sa.failed('read_pid', exclude_no_pid=False).reset_index(drop=True)

    # 分析mac wifibt failed項目
    x = sa.failed('wifibt', exclude_no_pid=False)
    xx = x.sort_values(['t0', 'pid']).reset_index(drop=True).reset_index()
    f_macaddr = xx.set_index(keys=['pid', 'index'])

    # failed summary
    f_summary = sa.summary()

    # AAB failed summary
    y = f_summary[f_summary.result.str.endswith('F')]
    fs = (df[df['pid'].isin(y.pid)].sort_values(['t0', 'pid'])
          .reset_index(drop=True).reset_index()
          .set_index(['pid', 'index']))

    # not very useful
    f0 = sa.failed()

    return fs, f_readpid, f_macaddr, f_summary


if __name__ == "__main__":

    writer = pd.ExcelWriter('SA_Analysis.xlsx', engine='xlsxwriter')

    station = 'SA'
    downloads_path = f'{stations_downloads[station]}'
    df = combine(downloads_path, station)
    sa = FailureAnalysis(df, station)

    fs, fr, fm, ss = SA_FA(sa)

    fs.to_excel(writer, sheet_name='summary')
    fr.to_excel(writer, sheet_name='read_pid failure')
    fm.to_excel(writer, sheet_name='mac_write failure')
    writer.save()
