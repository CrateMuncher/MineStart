from PyQt5 import QtWidgets, QtCore
import launcher

class MineStartAdvanced(QtWidgets.QMainWindow):
    change_to_basic = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()

        self.launcher = launcher.Launcher()

        self.main_widget = QtWidgets.QWidget()

        self.profiles = QtWidgets.QTreeWidget(self.main_widget)
