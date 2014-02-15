import os
from PyQt5 import QtWidgets
import launcher
import utils


class FirstStart(QtWidgets.QWizard):
    def __init__(self):
        super().__init__()

        self.interface_picker_page = QtWidgets.QWizardPage()

        self.addPage(InterfacePickerPage())
        self.show()


class InterfacePickerPage(QtWidgets.QWizardPage):
    def __init__(self):
        super().__init__()

    def initializePage(self):
        self.setTitle("Pick your preferred mode")
        self.radio_group = QtWidgets.QButtonGroup(self)

        self.radio_basic = QtWidgets.QRadioButton(
            """Basic mode
            This mode is for people who don't care about stuff like profiles
            and just want a launcher that works and looks good.
            To switch to Advanced mode, right-click on the background and click "Change to Advanced mode".""", self)
        self.radio_advanced = QtWidgets.QRadioButton(
            """Advanced mode
            This mode is for people who require more power than the basic mode,
            at the expense of not looking as good. This has full functionality like profiles, mods, and more.
            To switch to Basic mode, <DONT KNOW>.
            """, self)

        self.radio_group.addButton(self.radio_basic)
        self.radio_group.addButton(self.radio_advanced)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.radio_basic)
        vbox.addWidget(self.radio_advanced)

        self.setLayout(vbox)

    def validatePage(self):
        config = utils.Config(os.path.join(launcher.get_data_folder(), "ui_config.json"))
        if self.radio_basic.isChecked():
            config["mode"] = "basic"
        else:
            config["mode"] = "advanced"
        config.save()
        return True