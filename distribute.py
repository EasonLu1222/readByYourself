import re
import os
import json
from datetime import datetime
from shutil import copyfile, make_archive, rmtree
from distutils.dir_util import copy_tree
from utils import run


class Distribute:
    def __init__(self):
        self.ts = datetime.now().strftime("%Y%m%d_%H%M")
        self.STATION = [
            {
                "file_prefix": "第2站_主板",
                "station": "MainBoard"
            },
            {
                "file_prefix": "第3站_觸控板",
                "station": "CapTouch"
            },
            {
                "file_prefix": "第4站_燈板",
                "station": "LED"
            }
        ]

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
    d = Distribute()
    d.gen_version_num()
    d.gen_installer()
    d.make_zip()
    d.cleanup()
