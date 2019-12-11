import sys
import pandas as pd

pd.set_option('display.max_colwidth', 10)
pd.set_option('display.max_columns', 30)
pd.set_option('display.width', 1000)


def parse(path):
    #path = '/Users/zealzel/Downloads/Summary SAP109 - v1.2 - DVT1 - 191114 2019-11-20 08-11-51-0 UTC+0700.log'
    df = pd.read_csv(path, encoding='latin-1', sep='\t')
    DF = df[df.columns[:33]]
    c = DF.columns.values.tolist()
    cc = c[7:]
    ccc = [
        f'{e[1]}{e[0][8:]}{e[4].split(" ")[1]}'
        for e in [e.split(' - ') for e in cc]
    ]
    ccc = [e.replace('0', '') for e in ccc]
    ccc = [e.replace('Left', 'L') for e in ccc]
    ccc = [e.replace('Right', 'R') for e in ccc]
    ccc = [e.replace('Front', 'F') for e in ccc]

    cccc = ['date', 'time', 'utc', 'sn', 'user', 'db', 'all'] + ccc
    C = ['date', 'time', 'sn', 'all'] + ccc
    DF.columns = cccc
    DF = DF[C]

    kk = [
        'rbzL', 'rbzR',
        '2respL', '2levelL', '2rbzL',
        '2respR', '2levelR', '2rbzR',
        '4respF', '4levelF', '4rbzF',
    ]
    DF = DF[kk]

    return DF


def parse_dvt2_v1_3(path):
    #path = '/Users/zealzel/Downloads/Summary SAP109 - v1.2 - DVT1 - 191114 2019-11-20 08-11-51-0 UTC+0700.log'
    df = pd.read_csv(path, encoding='latin-1', sep='\t')
    DF = df[df.columns[:33]]
    c = DF.columns.values.tolist()
    cc = c[7:]
    ccc = [
        f'{e[1]}{e[0][8:]}{e[4].split(" ")[1]}'
        for e in [e.split(' - ') for e in cc]
    ]
    ccc = [e.replace('0', '') for e in ccc]
    ccc = [e.replace('Left', 'L') for e in ccc]
    ccc = [e.replace('Right', 'R') for e in ccc]
    ccc = [e.replace('Front', 'F') for e in ccc]

    cccc = ['date', 'time', 'utc', 'sn', 'user', 'db', 'all'] + ccc
    C = ['date', 'time', 'sn', 'all'] + ccc
    DF.columns = cccc
    DF = DF[C]

    kk = [
        'rbzL', 'rbzR',
        '2respL', '2levelL', '2rbzL',
        '2respR', '2levelR', '2rbzR',
        '4respF', '4levelF', '4rbzF',
    ]
    DF = DF[kk]

    return DF
