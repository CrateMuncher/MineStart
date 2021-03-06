import os
import sys

from PySide import QtGui

from interfaces.advanced import MineStartAdvanced
from interfaces.basic import MineStartBasic
from interfaces.firststart import FirstStart
import launcher
import utils


class MineStart(object):
    def main(self):
        self.app = QtGui.QApplication(sys.argv)
        self.app.setApplicationName("MineStart")

        self.ui_config = utils.Config(os.path.join(launcher.get_data_folder(), "ui_config.json"), {
            "mode": None,
            "basic": {},
            "advanced": {}
        })

        if self.ui_config["mode"] is None:
            self.window = FirstStart()
            self.window.finished.connect(self.first_start_finished)
        elif self.ui_config["mode"] == "basic":
            self.window = MineStartBasic()
            self.app.setStyleSheet("".join(open("assets/css/basic.css").readlines()))
            self.window.change_to_advanced.connect(self.change_to_advanced)
        else:
            self.window = MineStartAdvanced()
            self.app.setStyleSheet("".join(open("assets/css/advanced.css").readlines()))
            self.window.change_to_basic.connect(self.change_to_basic)
        self.refresh_things()

        sys.exit(self.app.exec_())

    def change_to_basic(self):
        self.window.close()
        self.window = MineStartBasic()
        self.app.setStyleSheet("".join(open("assets/css/basic.css").readlines()))
        self.window.change_to_advanced.connect(self.change_to_basic)
        self.refresh_things()
        self.ui_config.load()
        self.ui_config["mode"] = "basic"
        self.ui_config.save()

    def change_to_advanced(self):
        self.window.close()
        self.window = MineStartAdvanced()
        self.app.setStyleSheet("".join(open("assets/css/advanced.css").readlines()))
        self.window.change_to_basic.connect(self.change_to_basic)
        self.refresh_things()
        self.ui_config.load()
        self.ui_config["mode"] = "advanced"
        self.ui_config.save()

    def refresh_things(self):
        QtGui.QFontDatabase.addApplicationFont("assets/misc/Minecraftia.ttf")

    def first_start_finished(self):
        self.ui_config.load()
        if self.ui_config["mode"] == "basic":
            self.change_to_basic()
        else:
            self.change_to_advanced()

if __name__ == "__main__":
    MineStart().main()
