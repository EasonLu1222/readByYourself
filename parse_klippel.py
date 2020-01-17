import sys
import pandas as pd

pd.set_option('display.max_colwidth', 10)
pd.set_option('display.max_columns', 30)
pd.set_option('display.width', 1000)


def parse_dvt1_v1_2(path):
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


def parse_dvt2_v1_5(path):
    #path = '/Users/zealzel/Downloads/Summary SAP109 - v1.2 - DVT1 - 191114 2019-11-20 08-11-51-0 UTC+0700.log'
    df = pd.read_csv(path, encoding='latin-1', sep='\t')
    DF = df[df.columns[:41]]
    c = DF.columns.values.tolist()
    cc = c[7:]
    ccc = [
        f'{e[1]}{e[0][8:]}{e[4].split(" ")[1]}'
        for e in [e.split(' - ') for e in cc]
    ]
    #ccc = [e.replace('0', '') for e in ccc]
    ccc = [e.replace('Left', 'L') for e in ccc]
    ccc = [e.replace('Right', 'R') for e in ccc]
    ccc = [e.replace('Front', 'F') for e in ccc]

    cccc = ['date', 'time', 'utc', 'sn', 'user', 'db', 'all'] + ccc
    C = ['date', 'time', 'sn', 'all'] + ccc
    DF.columns = cccc
    DF = DF[C]

    '01respL', '01polL', '01thdL', '01rbzL', '01respR', '01polR', '01thdR', '01rbzR', '02respL', '02levelL', '02thdL', '02respR', '02levelR', '02thdR', '03rbzL', '03rbzR', '04rbzL', '04rbzR', '05rbzL', '05rbzR', '06rbzL', '06rbzR', '07rbzL', '07rbzR', '08rbzL', '08rbzR', '09respF', '09polF', '09thdF', '09rbzF', '10respF', '10levelF', '10thdF', '10rbzF'


    kk = [
        '02respL', '02respR',
        '03rbzL', '03rbzR',
        '04rbzL', '04rbzR',
        '05rbzL', '05rbzR',
        '06rbzL', '06rbzR',
        '07rbzL', '07rbzR',
        '08rbzL', '08rbzR',
        '10respF','10rbzF',
    ]
    DF = DF[kk]

    return DF


def parse_dvt2_v1_7(path):
    #path = '/Users/zealzel/Downloads/Summary SAP109 - v1.2 - DVT1 - 191114 2019-11-20 08-11-51-0 UTC+0700.log'
    df = pd.read_csv(path, encoding='latin-1', sep='\t')

    DF = df[df.columns[:35]]
    c = DF.columns.values.tolist()
    cc = c[7:]

    ccc = [
        f'{e[1]}{e[0][8:]}{e[4].split(" ")[1]}'
        for e in [e.split(' - ') for e in cc]
    ]
    ccc = [e.replace('Left', 'L') for e in ccc]
    ccc = [e.replace('Right', 'R') for e in ccc]
    ccc = [e.replace('Front', 'F') for e in ccc]

    cccc = ['date', 'time', 'utc', 'sn', 'user', 'db', 'all'] + ccc
    C = ['date', 'time', 'sn', 'all'] + ccc

    DF.columns = cccc
    DF = DF[C]

    '01respL', '01polL', '01thdL', '01rbzL', '01respR', '01polR', '01thdR', '01rbzR', '02respL', '02levelL', '02thdL', '02respR', '02levelR', '02thdR', '03rbzL', '03rbzR', '04rbzL', '04rbzR', '05rbzL', '05rbzR', '06rbzL', '06rbzR', '07rbzL', '07rbzR', '08rbzL', '08rbzR', '09respF', '09polF', '09thdF', '09rbzF', '10respF', '10levelF', '10thdF', '10rbzF'


    kk = [
        '01rbzL', '01rbzR',
        '02respL', '02thdL', '02respR', '02thdR',
        '03rbzL', '03rbzR',
        '04rbzL', '04rbzR',
        '05rbzL', '05rbzR',
        '06rbzF',
        '07respF', '07thdF', '07rbzF',
    ]
    DF = DF[kk]

    return DF
