import os
import sys
import json
import pythoncom
import win32com.client as client
import pandas as pd


class BSndChk(object):
    def __init__(self):  # 初始化2：設定預設物件欄位
        self.test_item, self.test_result = [], []
        self.arrayX, self.arrayY, self.arrayZ = [], [], []
        self.header = [
            'Out', 'In', 'Cat', 'Step', 'Pass/Fail', 'Margin', 'Limits'
        ]
        self.paramNames = [
            "Command", "Success?", "Pass?", "Margin", "Table", "Xdatapoints",
            "Ydatapoints", "Zdatapoints"
        ]

    def LinkSC(self):
        pythoncom.CoInitialize()
        self.ScApp = client.Dispatch("SoundCheck111.Application")
        self.vi = self.ScApp.GetVIReference("ControlSC.vi")
        self.vi._FlagAsMethod("Call")  # Call=>Method # 不然有可能叫不到

    def getFuncNm(self):
        return sys._getframe(1).f_code.co_name

    def ByRefVar(self, var):
        return client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, var)

    def Open_Sequence(self, SqzPath):
        print(f'[SoundCheck] 開始讀取{SqzPath}')
        paramValues = [
            "open " + SqzPath, False, False, 0.0, "", self.arrayX, self.arrayY,
            self.arrayZ
        ]
        newNm = self.ByRefVar(self.paramNames)
        newVal = self.ByRefVar(paramValues)
        self.LinkSC()
        self.vi.Call(newNm, newVal)
        self.test_result = ''
        self.test_item = ''
        self.test_item = newNm.value  # 存到測項
        print(f'[SoundCheck] 讀取成功')

    def Run_Sequence(self):
        print(f'[SoundCheck] 開始測試')
        paramValues = [
            "run", False, False, 0.0, "", self.arrayX, self.arrayY, self.arrayZ
        ]
        newNm = self.ByRefVar(self.paramNames)
        newVal = self.ByRefVar(paramValues)
        if self.test_item == []:  # 如果為空 代表還沒有讀入SQZ 不繼續
            return
        self.LinkSC()
        self.test_result = ''
        self.vi.Call(newNm, newVal)
        self.test_result = newNm.value  # 存到測項
        results = self.test_result[4].strip().split('\n')
        print('results', results)
        print(
            f'[SoundCheck] 測試完成：{self.test_result[1]} 測試通過：{self.test_result[2]}'
        )

        df = self.test_rst_Table
        xx = df.iloc[5:8, 4:6].values.tolist()
        x = [f'{e[0].capitalize()}({e[1]})' for e in xx] # RF/RubBuzz/THD
        res = x[0], x[2], x[1]
        return res

    @property
    def test_rst_Table(self):
        res = []
        if len(self.test_item) > 0:
            list1 = [
                row.split('\t') for row in self.test_item[4].split('\r\n')
                if row != ''
            ]
        else:
            list1 = [['ERROR：請先讀取Sequence']]
        if len(self.test_result) > 0:
            list2 = [
                row.split('\t') for row in self.test_result[4].split('\r\n')
                if row != ''
            ]
        else:
            list2 = [
                (len(self.header) - len(list1[0])) * ','.split(',')  # 未測試 先補空值
                for row in range(len(list1))
            ]
        for idx, _ in enumerate(list1):
            x = list1[idx] + list2[idx]
            res.append(x)
        df = pd.DataFrame(res, columns=self.header)
        return df


if __name__ == "__main__":
    b = BSndChk()
    b.LinkSC()
    sqz_path = os.path.join(os.path.abspath(os.path.curdir), 'Sequence',
                            'James', 'test_20181030_one failed',
                            'test_one_failed.sqc')
    b.Open_Sequence(sqz_path)
    import time; time.sleep(1)
    b.Run_Sequence()

