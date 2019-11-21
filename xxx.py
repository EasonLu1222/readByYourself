import pyautogui as pag


win = pag.getWindowsWithTitle('SAP109 - v1.2 - DVT1')[0]
win.activate()
win.maximize()
pag.click(127, 80)
pag.click(127, 80)
pag.typewrite('SAP109XXXXXAAAAA2')
#pag.typewrite('ACD_ACD')
pag.typewrite('\n\r')
