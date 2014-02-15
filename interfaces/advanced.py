from PyQt5 import QtWidgets
import launcher

class MineStartAdvanced(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.launcher = launcher.Launcher()

