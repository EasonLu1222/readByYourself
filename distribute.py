import re
import os
import sys
import json
from datetime import datetime
from shutil import copyfile, make_archive, rmtree
from distutils.dir_util import copy_tree
from utils import run
import argparse


class Distribute:
    def __init__(self, stations=None):
        self.ts = datetime.now().strftime("%Y%m%d_%H%M")
        STATIONS = [
            {
                "station": "MainBoard",
                "file_prefix": "第02站_主板",
            },
            {
                "station": "CapTouchMic",
                "file_prefix": "第03站_觸控板",
            },
            {
                "station": "LED",
                "file_prefix": "第04站_燈板",
            },
            {
                "station": "RF",
                "file_prefix": "第05站_BtWiFi",
            },
            {
                "station": "Audio",
                "file_prefix": "第06站_Audio",
            },
            {
                "station": "Leak",
                "file_prefix": "第07站_Leak",
            },
            {
                "station": "WPC",
                "file_prefix": "第08站_WPC",
            },
            {
                "station": "PowerSensor",
                "file_prefix": "第09站_Antenna",
            },
            {
                "station": "SA",
                "file_prefix": "第10站_SA",
            },
            {
                "station": "Acoustic",
                "file_prefix": "第11站_Acoustic",
            },
            {
                "station": "Download",
                "file_prefix": "第12站_Download",
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
    d.make_zip()
    d.cleanup()
