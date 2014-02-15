import sys
from PyQt5 import QtWidgets, QtGui
from interfaces.basic import MineStartBasic

class MineStart(object):
    def main(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setApplicationName("MineStart")

        self.window = MineStartBasic()


        self.window.change_to_advanced.connect(self.change_to_basic)

        self.refresh_things()

        sys.exit(self.app.exec_())

    def change_to_basic(self):
        self.window.close()
        self.window = MineStartBasic()
        self.refresh_things()

    def change_to_advanced(self):
        self.window.close()
        self.refresh_things()

    def refresh_things(self):
        self.app.setStyleSheet("".join(open("assets/style.css").readlines()))
        QtGui.QFontDatabase.addApplicationFont("assets/Minecraftia.ttf")

if __name__ == "__main__":
    MineStart().main()
