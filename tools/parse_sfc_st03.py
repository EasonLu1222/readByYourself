import requests
from operator import itemgetter
import pandas as pd
from bs4 import BeautifulSoup


def find_page(page=1):
    url = 'http://10.228.14.99:8109/search/Query_ST03.asp?g_flag=1&goPageFlag=1'
    files = {
      'g_result': 'ALL',
      'goPage': page,
      'g_search1': '2020/01/01',
      'g_search2': '2020/02/28'
    }
    R = requests.post(url, data=files)
    X = BeautifulSoup(R.text, features='html.parser')
    XX = X.find_all('table', id='table1')[0].find_all('tr')[1:]
    XXX = [itemgetter(1,4)(e.find_all('td')) for e in XX]
    pid_msn = [(i.text, j.text) for i,j in XXX]
    return pid_msn


if __name__ == "__main__":
    result = []
    for i in range(1, 999):
        print('page', i)
        pid_msn = find_page(i)
        if len(pid_msn) > 0:
            result.append(pid_msn)
        else:
            break
    result = sum(result, [])
    df = pd.DataFrame(result, columns=['asn', 'msn'])
    if len(df[df.msn.duplicated()]) > 0:
        print('msn has duplicated data!')
