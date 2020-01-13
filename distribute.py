import re
import os
import json
from datetime import datetime
from shutil import copyfile, make_archive, rmtree
from distutils.dir_util import copy_tree
from utils import run, get_md5
import argparse


class Distribute:
    def __init__(self, stations=None):
        self.ts = datetime.now().strftime("%Y%m%d_%H%M")
        STATIONS = [
            {
                "station": "MainBoard",
                "file_prefix": "Station02_MainBoard",
            },
            {
                "station": "MainBoardIqc",
                "file_prefix": "Station01_MainBoardIqc",
            },
            {
                "station": "CapTouchMic",
                "file_prefix": "Station03_SwBoard",
            },
            {
                "station": "LED",
                "file_prefix": "Station04_LedBoard",
            },
            {
                "station": "RF",
                "file_prefix": "Station05_BtWiFi",
            },
            {
                "station": "AudioListen",
                "file_prefix": "Station06_AudioListen",
            },
            {
                "station": "Leak",
                "file_prefix": "Station07_Leak",
            },
            {
                "station": "WPC",
                "file_prefix": "Station08_WPC",
            },
            {
                "station": "PowerSensor",
                "file_prefix": "Station09_Antenna",
            },
            {
                "station": "SA",
                "file_prefix": "Station10_SA",
            },
            {
                "station": "AcousticListen",
                "file_prefix": "Station11_AcousticListen",
            },
            {
                "station": "Download",
                "file_prefix": "Station12_Download",
            },
            {
                "station": "BTMacFix",
                "file_prefix": "StationXX_BTMacFixDownload",
            },
            {
                "station": "MicBlock",
                "file_prefix": "Station13_MicBlock",
            },
        ]
        if stations:
            self.STATION = [e for e in STATIONS if e['station'] in stations]
        else:
            self.STATION = STATIONS
        print(self.STATION)

    def gen_version_num(self):
        """
        Use the result of 'git describe' as version number
        Insert the version number to app.py
        """
        # Get version number from git
        ver = run("git describe")
        ver = ver.strip()

        # Read app.py
        with open("./app.py", "r", encoding="utf-8") as f:
            contents = f.read()

        # Replace insert the version number to app.py
        # new_content = contents.replace('version = ""', f'version = "{ver}"')
        new_content = re.sub("version = \".*\"", f'version = "{ver}_{self.ts}"', contents)

        # Write app.py
        with open("./app.py", "w", encoding="utf-8") as f:
            f.write(new_content)

    def gen_installer(self):
        """
        Run pyinstaller to generate installer file.
        The generated files are as follow:
            dist/app.exe
            dist/jsonfile
        """
        output = run("pyinstaller --onefile app.spec")
        print(output)

    def gen_checksum(self):
        md5_hash = get_md5("dist/app.exe")
        with open('dist/md5.txt', 'w') as f:
            f.write(md5_hash)

    def make_zip(self):
        """
        1. Create folders for each station defined in self.STATION with current datetime as suffix
        2. Copy app.exe and jsonfile to those folders
        3. Rename app.exe to app_DATETIME.exe
        4. Modify station.json in each folder
        5. Zip those folders
        """

        for sta in self.STATION:
            target_dir = f"dist/{sta['file_prefix']}_{self.ts}"
            os.mkdir(target_dir)
            copyfile("dist/app.exe", f"{target_dir}/app_{self.ts}.exe")
            copyfile("dist/md5.txt", f"{target_dir}/md5.txt")
            copy_tree("dist/jsonfile", f"{target_dir}/jsonfile")

            if sta['station']=='RF':
                copy_tree("dist/iqxel", f"{target_dir}/iqxel")

            sta_obj = {"STATION": sta["station"]}
            station_json_path = f"dist/{sta['file_prefix']}_{self.ts}/jsonfile/station.json"
            with open(station_json_path, "w") as outfile:
                json.dump(sta_obj, outfile)

            make_archive(target_dir, "zip", target_dir)
            rmtree(target_dir)

    def cleanup(self):
        """
        Undo the change in app.py
        Returns:

        """
        with open("./app.py", "r", encoding="utf-8") as f:
            contents = f.read()

        new_content = re.sub("version = \".*\"", 'version = ""', contents)

        with open("./app.py", "w", encoding="utf-8") as f:
            f.write(new_content)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('stations', help='station names', type=str, nargs='*',
                        metavar='c')
    args = parser.parse_args()
    stations = args.stations

    d = Distribute(stations)
    d.gen_version_num()
    d.gen_installer()
    d.gen_checksum()
    d.make_zip()
    d.cleanup()
