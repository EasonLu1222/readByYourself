import inspect
import os
import argparse
import re
import sys
import time
import json
from serial import Serial, SerialException       #這裡的serial為python模組
from datetime import datetime
from subprocess import Popen, PIPE
from pydub import AudioSegment

from mylogger import logger
from config import station_json

PADDING = ' ' * 8                                                      #PADDING為8個空字串


    #功能為對serial下指令並轉為utf-8'，並檢查回傳值解碼是否有異常
def issue_command(serial, cmd):                                        #定義方法對serial發出命令
    serial.write(f'{cmd}\n'.encode('utf-8'))                           #對serial下命令
    lines = serial.readlines()                                         #讀取sreial回傳字串設定=lines
    lines_encoded = []                                                 #設定lines_encoded = []為空序列列表
    for e in lines:                                                    #lines為serial回傳的字串;將每一個lines對做下面定義
        try:
            line = e.decode('utf-8')                                   #將所得的字串編碼為utf-8
        except UnicodeDecodeError as ex:                               #假設有錯誤的解碼
            logger.info("ignored unicode error")                       #日誌紀錄輸出ignored unicode error
        except Exception as ex:                                        #Exception發生時，抓它發生的位置以及詳細原因
            logger.info(f"Error: {ex}")                                #日誌輸出異常的UnicodeDecodeError訊息代碼
        else:
            lines_encoded.append(line)                                 #將line編碼完成的字串設定lines_encoded = []為空序列列表
    return lines_encoded                                               #回傳lines_encoded

    #用來記錄轉碼後的下cmd與serial回傳日誌
def run(portname, cmd, baudrate=115200, timeout=0.2):                  #定義方法run屬性portname, cmd, baudrate=115200, timeout=0.2
    with Serial(portname, baudrate=baudrate, timeout=timeout) as ser:  #將Serial回傳給ser，serial基本模組的Serial API
        lines = issue_command(ser, cmd)                                #引進方法def issue_command(並將ser,cmd)目的為輸出日誌有serial回傳和下cmd資訊
        logger.info(lines)
    return lines

    #這隻程式是對mic_block處理;所以定死在MicBlock工站，依工照獲取相對應json檔(設為屬性值)
def get_json_val_by_attr(attr):                                        #這裡的方法為獲取jason檔裡的設定值獲得屬性
    json_name = station_json['MicBlock']                               #定義由config獲取的station_json;工站和對應檔案json數值;=MicBlocke工站時
    jsonfile = f'jsonfile/{json_name}.json'                            #由工站名獲取對應的json檔
    json_obj = json.loads(open(jsonfile, 'r', encoding='utf8').read()) #打開對應的json檔並轉換為utf8格式;引入json_obj
    return json_obj[attr]                                              #回傳到json_obj[attr]

    #由get_json_val_by_attr獲得v14_mic_block.json
    #v14_mic_block.json獲得通道COM12,
    #並下cmd指令撥放檔案f"aplay /usr/share/1000hz_4s.wav"
    #並檢查serial 回傳lines是否有找到檔案
    #並檢查serial 是否有異常
def play_tone():                                                       #開始撥放
    com = get_json_val_by_attr("speaker_com")                          #獲取v14_mic_block.json裡的item speaker_com為COM12
    logger.debug(f"{PADDING}speaker_com: {com}")                       #日誌紀錄為        speaker_com: COM12
    try:
        # simulate press enter & ignore all the garbage
        run(com, "")                                                   #對COM下空字串清除清空

        lines = run(com, f"aplay /usr/share/1000hz_4s.wav")            #執行def run :為com:COM12,cmd:aplay /usr/share/1000hz_4s.wav

        #serial回傳lines利用正則表達式比對字串such file or directory;代表沒有找到檔案輸出result = f'Fail(missing 1000hz file);
        #如果有找到則輸出result = Pass
        result = f'Fail(missing 1000hz file)' if any(re.search("such file or directory", e) for e in lines) else 'Pass'
    except SerialException as e:                                       #偵測Serial看是否有異常
        logger.error(f'{e}')                                           #如果有紀錄日誌
        result = 'Fail(bad serial port)'                               #輸出結果為Fail(bad serial port)
    return result                                                      #回傳結果值

    #觸發測試
def trigger_block():                                            #定義觸發模塊
    com = get_json_val_by_attr("valve_com")                     #獲得json檔裡的valve_com設定COM1
    try:
        valve_signal_ok = False                                 #設定旗標valve_signal_ok = False
        with Serial(com, baudrate=19200, timeout=1) as ser:     #設定serial com為COM1;並將回傳值給ser
            cmd = "1"                                           #並下命令cmd =1
            ser.write(f'{cmd}\n'.encode('utf-8'))               #對serial 寫入cmd ;cmd先轉碼為utf-8
            while True:
                l = ser.readline().strip()                      #讀取serail回應加上strip用于去除字符串首尾的字符，默认是空格、\n、\t回傳l
                logger.debug(f"Readline result: {l}")           #輸出日誌;並記錄Readline result: 回傳結果
                if l == b'2':                                   #如果回傳b=二進制2
                    valve_signal_ok = True                      #代表valve_signal_ok 測試完畢 旗標拉起來為True
                    break                                       #強制跳脫

        result = f'Pass' if valve_signal_ok else 'Fail'         #利用valve_signal_ok判斷是True還是False 輸出結果
    except SerialException as e:                                #偵測serial是否有異常將值傳給e
        logger.error(f'{e}')                                    #輸出異常結果訊息日誌
        result = 'Fail(bad serial port)'                        #結果輸出為Fail(bad serial port)
    return result                                               #回傳到result


    #發送最後測試結果送至治具
def sent_final_test_result_to_fixture(is_all_dut_pass):        #定義方法引進屬性is_all_dut_pass如果所有的杜比都通過測試
    com = get_json_val_by_attr("valve_com")                    #由方法獲得屬性值com=COM1
    rtn = "4" if is_all_dut_pass else "3"                      #is_all_dut_pass=True=4;is_all_dut_pass=False=3;由主程式app.py給出is_all_dut_pass值
    try:
        lines = run(com, rtn, baudrate=19200, timeout=0.2)     #對serial 下com=COM1,cmd=4 or3
    except SerialException as e:                               #偵測serial是否異常傳給e變數
        logger.error(f'{e}')                                   #記錄異常日誌

    #生成實驗目錄資料夾依照年月日命名
def make_experiment_dir():                                     #做實驗目錄
    now = datetime.now().strftime('%Y%m%d')                    #獲取現在時間的年月日
    dir = f"./wav/experiment_{now}"                            #目錄為目錄底下的wav資料夾
    if not os.path.exists(dir):                                #如果目錄資料夾不存在
        os.makedirs(dir)                                       #在目錄底下新生成資料夾
    return dir                                                 #回傳

    # 關閉Google Voice Assistant，谷歌語音助理
def turn_off_gva():                                            #關閉Google Voice Assistant，谷歌語音助理
    cmd = 'setprop ctl.stop mute_service'                      #adb 命令setprop ctl.stop停止mute_service
    run(portname, cmd)

    #停播，是要讓GVA的程序停止運行();這個/chrome/cast_cli會佔用麥克風，因為他要時時刻刻聽喚醒詞
    cmd = '/chrome/cast_cli stop cast'
    run(portname, cmd)

    #間檢查mic是否靜音;確認不是;開始錄音
def record_sound(save_path, duration):                       #save_path存檔路徑;duration
    cmd = 'i2cget -f -y 1 0x1f 0x02'                         #讀取i2cget -f -y 1 0x1f 0x02    #回傳0x00代表unmute;mic被開啟, 0x01代表mute
    lines = run(portname, cmd)                               #對serial下命令
    if lines[1].rstrip() == '0x01':                          #serial回傳0x01代表靜音mic被關閉#rstrip() 删除 string 字符串末尾的指定字符（默认为空格）
        logger.info("Error: the mic is muted")               #則日誌輸出Error: the mic is muted
        return 0                                             #回傳值為0

    #錄音arecord -Dhw:0,3 -c 2 -r 48000 -f S32_LE -d 秒數 檔名.wav
    cmd = f'arecord -Dhw:0,3 -c 2 -r 48000 -f S32_LE -d {duration} {save_path}'
    run(portname, cmd)
    return 1                                                #回傳值為1

    #使用adb抓檔案透過subprocess模組
def pull_result(save_path, dest_path):                              #使用adb抓檔案
    proc = Popen(['adb', 'pull', save_path, dest_path], stdout=PIPE)
    outputs, _ = proc.communicate()

    #將錄音檔轉為dbfs
def get_dbfs(wav_path, dir_path):
    s = AudioSegment.from_wav(wav_path)                             #讀取錄音音源檔wav_path為錄音源;dir_path為轉檔dBFS後的储存檔案
    s_cut = s[1000:]                                                #對音源做切片(取最後到往前1000ms)
    ss = s_cut.split_to_mono()                                      #分割2個通道以上

    with open(f'{dir_path}/test_result.txt', 'a') as f:             #打開test_result.txt(有製具壓和沒製具壓寫入時間點錯開)
          f.writelines(f'{ss[0].dBFS},{ss[1].dBFS}\n')              #傳給分別寫入2個聲道存到test_result.txt

    logger.info(f'{wav_path}\t{s.dBFS}\n')                          #日誌紀錄錄音檔路徑\t:Tab鍵

    return s.dBFS

    #這裡是主要的測試流程安排(沒有制具壓mic)
def mic_test(portname):
    now = datetime.now().strftime('%Y%m%d')                         #定義now為現在時間年月日
    dir_path = f"./wav/experiment_{now}"                            #定義dir_path為打開現在時間資料夾
    # parser = argparse.ArgumentParser()
    # parser.add_argument('ports', help='serial com port names', type=str)
    # parser.add_argument('filename', help='filename', type=str)
    # args = parser.parse_args()
    save_path = f'/usr/share/mic_record.wav'                        #定義save_path為/usr/share/mic_record.wav

    dir = make_experiment_dir()                                     #呼叫def make_experiment_dir 創建資料夾

    duration = 3                                                    #設定錄音時間為3秒
    turn_off_gva()                                                  #關閉google助理
    rtn = record_sound(save_path, duration)                         #呼叫def record_sound開始錄音成功rtn回傳1;失敗回傳0

    if rtn == 1:                                                    #rtn == 1時代表成功
        time.sleep(duration+1)                                      #等待時間為錄音時間多加1sec
        pull_result(save_path, dir)                                 #呼叫抓檔函示pull_result
        cmd = 'rm /usr/share/mic_record.wav'                        #定義cmd
        run(portname, cmd)                                          #對serial下cmd和收serial回應
        wav_path = f'{dir}/mic_record.wav'                          #存檔錄音的路徑
        get_dbfs(wav_path, dir)                                     #呼叫get_dbfs轉檔錄音檔並存檔在test_result.txt
        with open(f'{dir_path}/test_result.txt', "r") as f:         #打開檔案並傳給f
            line = f.readlines()[0]                                 #將serial讀取第0行的位置
            mic_r, mic_l = [float(e) for e in line.split(",")]      #看到","號分開有左聲道和右聲道
        result = f'Pass(L:{mic_l:.3f}, R:{mic_r:.3f})'              #結果為pass輸出Pass(L:{mic_l:.3f}, R:{mic_r:.3f})為小數點後面3位
        return result
    if rtn == 0:                                                    #如果rtn = 0代表測試失敗
        result = 'Fail(mic is muted)'                               #結果為Fail(mic is muted)
        return result


def mic_test_block(portname):
    now = datetime.now().strftime('%Y%m%d')                          #定義now為現在時間年月日
    dir_path = f"./wav/experiment_{now}"                             #定義路徑
    # parser = argparse.ArgumentParser()
    # parser.add_argument('ports', help='serial com port names', type=str)
    # parser.add_argument('filename', help='filename', type=str)
    # args = parser.parse_args()
    save_path = f'/usr/share/mic_block_record.wav'                  #定義純檔路徑

    dir = make_experiment_dir()                                     #創建資料夾

    duration = 3                                                    #定義錄音時間
    turn_off_gva()                                                  #關閉google助理
    rtn = record_sound(save_path, duration)                         #錄音檔存檔

    if rtn == 1:
        time.sleep(duration + 1)                                    #等待時間
        pull_result(save_path, dir)
        cmd = 'rm /usr/share/mic_block_record.wav'
        run(portname, cmd)
        wav_path = f'{dir}/mic_block_record.wav'
        get_dbfs(wav_path, dir)
        with open(f'{dir_path}/test_result.txt', "r") as f:
            line = f.readlines()[1]
            mic_r, mic_l = [float(e) for e in line.split(",")]
        result = f'Pass(L:{mic_l:.3f}, R:{mic_r:.3f})'
        return result
    if rtn == 0:
        result = 'Fail(mic is muted)'
        return result


def calculate_sensitivity():                                        #計算
    rtn = ""                                                        #
    now = datetime.now().strftime('%Y%m%d')                         #定義現在時間
    dir_path = f"./wav/experiment_{now}"                            #定義要開啟的資料夾
    try:
        with open(f'{dir_path}/test_result.txt', "r") as f:         #開啟txt檔
            line = f.readline()
            mic_channel = line.split(",")                           #mic聲道用,分開
            line = f.readline()
            mic_block_channel = line.split(",")                     #
    except Exception as e:                                          #偵測serial是否異常
        logger.error(f'{PADDING}{e}')
        return 'Fail(read test result failed)'

    os.remove(f'{dir_path}/test_result.txt')                        #分析完後移動資料

    channel_r_diff = float(mic_channel[0]) - float(mic_block_channel[0])
    channel_l_diff = float(mic_channel[1]) - float(mic_block_channel[1])

    # If one mic channel is broken, the system will copy the data from the good channel to the bad channel,
    # which makes the data of the 2 channels identical. This is a convenient way to judge if one mic is broken.
    mic_r = float(mic_channel[0])                                 #制具未遮的右聲道
    mic_l = float(mic_channel[1])                                 #制具未遮的左聲道
    mic_b_r = float(mic_block_channel[0])                         #制具有遮的右聲道
    mic_b_l = float(mic_block_channel[1])                         #制具有遮的左聲道
    is_one_mic_broken = abs(mic_r - mic_l) < 0.001 and abs(mic_b_r - mic_b_l) < 0.001#左聲道和右聲道相減差異值

    logger.info(f"mic_channel_left: {mic_channel[1]}")                 #獲得日誌訊息
    logger.info(f"mic_channel_right: {mic_channel[0]}")                #獲得日誌訊息
    logger.info(f"mic_block_channel_left: {mic_block_channel[1]}")     #獲得日誌訊息
    logger.info(f"mic_block_channel_right: {mic_block_channel[0]}")    #獲得日誌訊息
    logger.info(f"channel_left_diff: {channel_l_diff}")                #獲得日誌訊息
    logger.info(f"channel_right_diff: {channel_r_diff}")               #獲得日誌訊息

    if channel_r_diff >= 20 and channel_l_diff >= 20 and not is_one_mic_broken:  #如果大於20為Fail回傳rtn;小於20回傳pass rtn
        rtn = "Pass"
    else:
        rtn = "Fail"

    channel_r_diff_fmt = "%.3f" % channel_r_diff    # Round the float to 3 decimal places and convert it to str:將浮點數舍入到小數點後三位並將其轉換為str
    channel_l_diff_fmt = "%.3f" % channel_l_diff    # e.g. 3.1415926 -> "3.142"將浮點數舍入到小數點後三位並將其轉換為str
    rtn += f"(L:{channel_l_diff_fmt}, R:{channel_r_diff_fmt})"

    return rtn


if __name__ == "__main__":
    thismodule = sys.modules[__name__]

    logger.info(f'{PADDING}task_runeach start...')                      #開始啟動
    parser = argparse.ArgumentParser()                                  #
    parser.add_argument('-p',
                        '--portname',
                        help='serial com port name',
                        type=str)
    parser.add_argument('-i', '--dut_idx', help='dut #number', type=int)
    parser.add_argument('-s', '--dynamic_info', help='serial id', type=str)
    parser.add_argument('funcname', help='function name', type=str)
    args = parser.parse_args()
    portname, dut_idx, dynamic_info = [
        getattr(args, e) for e in ('portname', 'dut_idx', 'dynamic_info')
    ]
    funcname = args.funcname

    logger.info(f'{PADDING}portname: {portname}')
    logger.info(f'{PADDING}dut_idx: {dut_idx}')
    logger.info(f'{PADDING}dynamic_info: {dynamic_info}')
    logger.info(f'{PADDING}args: {args}')
    logger.info(f'{PADDING}funcname: {funcname}')

    func = getattr(thismodule, funcname)
    func_args = [
        getattr(thismodule, arg) for arg in inspect.getfullargspec(func).args
    ]
    logger.info(f'{PADDING}func_args: {func_args}')

    result = func(*func_args)
    if result:
        sys.stdout.write(result)

    logger.info(f'{PADDING}task_runeach end...')
