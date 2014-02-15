import json
import threading
from PyQt5 import QtWidgets, QtCore, QtGui
import requests
import launcher


class MineStartAdvanced(QtWidgets.QMainWindow):
    change_to_basic = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.launcher = launcher.Launcher()

        logged_in = len(self.launcher.user_accounts) > 0
        while not logged_in:
            try:
                form = LoginForm()
                form.exec_()
                self.launcher.authenticate_password(form.email(), form.password())
                logged_in = True
            except launcher.InvalidCredentialsError:
                pass

        self.main_widget = QtWidgets.QWidget()

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.addAction(QtGui.QIcon("assets/icons/user_add.png"), "Add Profile")
        self.toolbar.addAction(QtGui.QIcon("assets/icons/user_delete.png"), "Remove Profile")
        self.toolbar.addAction(QtGui.QIcon("assets/icons/play.png"), "Play Game")
        self.toolbar.addAction(QtGui.QIcon("assets/icons/settings.png"), "Profile Options")

        self.player_chooser = QtWidgets.QComboBox()
        self.player_chooser.setIconSize(QtCore.QSize(32, 32))
        for number, user_account in enumerate(self.launcher.user_accounts.values()):
            self.player_chooser.insertItem(number, user_account.username)

            def apply_face(icon):
                self.player_chooser.setItemIcon(number, icon)

            self.player_chooser.setItemIcon(number, QtGui.QIcon("assets/profile_icons/steve.png"))

            face_retriever = FaceRetrieverThread(user_account.username)
            face_retriever.retrieved.connect(apply_face)
            face_retriever.start()

        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)
        self.removeToolBarBreak(self.toolbar)

        self.profiles = QtWidgets.QListWidget(self.main_widget)
        self.profiles.setObjectName("AdvancedProfileList")
        self.profiles.setViewMode(QtWidgets.QListView.IconMode)
        self.profiles.setMovement(QtWidgets.QListView.Static)
        self.profiles.setIconSize(QtCore.QSize(64, 64))

        for profile in self.launcher.profiles.values():
            def settings():
                self.open_settings(profile)

            item = QtWidgets.QListWidgetItem(QtGui.QIcon("assets/profile_icons/steve.png"), profile.name)
            self.profiles.addItem(item)
            if profile == self.launcher.current_profile:
                item.setSelected(True)

        self.status_up_pixmap = QtGui.QPixmap("assets/lamp/redstone_lamp_on.png")
        self.status_down_pixmap = QtGui.QPixmap("assets/lamp/redstone_lamp_off.png")

        self.uptime_skins = QtWidgets.QLabel()
        self.uptime_session = QtWidgets.QLabel()
        self.uptime_website = QtWidgets.QLabel()
        self.uptime_realms = QtWidgets.QLabel()
        self.uptime_login = QtWidgets.QLabel()
        self.uptime_text = QtWidgets.QLabel()
        self.refresh_status()

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)

        # self.launch_button = QtWidgets.QPushButton("Launch Minecraft!", self.main_widget)
        # self.launch_button.setObjectName("AdvancedLaunchButton")

        top_hbox = QtWidgets.QHBoxLayout()

        bottom_hbox = QtWidgets.QHBoxLayout()

        bottom_hbox.addWidget(self.uptime_skins)
        bottom_hbox.addWidget(self.uptime_session)
        bottom_hbox.addWidget(self.uptime_website)
        bottom_hbox.addWidget(self.uptime_realms)
        bottom_hbox.addWidget(self.uptime_login)
        bottom_hbox.addWidget(self.uptime_text)
        bottom_hbox.addStretch(1)
        bottom_hbox.addWidget(QtWidgets.QLabel("Welcome,"))
        bottom_hbox.addWidget(self.player_chooser)

        main_vbox = QtWidgets.QVBoxLayout()
        main_vbox.addLayout(top_hbox)
        main_vbox.addWidget(self.profiles)
        main_vbox.addLayout(bottom_hbox)

        self.main_widget.setLayout(main_vbox)
        self.setCentralWidget(self.main_widget)
        self.resize(854, 480)
        self.show()

    def edit_profile_field(self, item, column):
        if column not in [1]:  # Disallowed!
            self.profiles.editItem(item, column)

    def open_settings(self, profile):
        pass

    def refresh_status(self):
        def update_ui(json_str):
            resp = json.loads(json_str)
            report = resp["report"]

            up = 0

            if report["skins"]["status"] == "up":
                up += 1
                self.uptime_skins.setPixmap(self.status_up_pixmap)
                self.uptime_skins.setToolTip("Minecraft Skins: " + "Up")
            else:
                self.uptime_skins.setPixmap(self.status_down_pixmap)
                self.uptime_skins.setToolTip("Minecraft Skins: " + "Down")

            if report["session"]["status"] == "up":
                up += 1
                self.uptime_session.setPixmap(self.status_up_pixmap)
                self.uptime_session.setToolTip("Minecraft Session: " + "Up")
            else:
                self.uptime_session.setPixmap(self.status_down_pixmap)
                self.uptime_session.setToolTip("Minecraft Session: " + "Down")

            if report["website"]["status"] == "up":
                up += 1
                self.uptime_website.setPixmap(self.status_up_pixmap)
                self.uptime_website.setToolTip("Minecraft Website: " + "Up")
            else:
                self.uptime_website.setPixmap(self.status_down_pixmap)
                self.uptime_website.setToolTip("Minecraft Website: " + "Down")

            if report["realms"]["status"] == "up":
                up += 1
                self.uptime_realms.setPixmap(self.status_up_pixmap)
                self.uptime_realms.setToolTip("Minecraft Realms: " + "Up")
            else:
                self.uptime_realms.setPixmap(self.status_down_pixmap)
                self.uptime_realms.setToolTip("Minecraft Realms: " + "Down")

            if report["login"]["status"] == "up":
                up += 1
                self.uptime_login.setPixmap(self.status_up_pixmap)
                self.uptime_login.setToolTip("Minecraft Login: " + "Up")
            else:
                self.uptime_login.setPixmap(self.status_down_pixmap)
                self.uptime_login.setToolTip("Minecraft Login: " + "Down")

            if up < 1:
                self.uptime_text.setText("All services down")
            elif up < 5:
                self.uptime_text.setText("Some services down")
            else:
                self.uptime_text.setText("All services up")

        self.refresh_thread = FetchString("http://xpaw.ru/mcstatus/status.json")
        self.refresh_thread.fetched.connect(update_ui)
        self.refresh_thread.start()

class Settings(QtWidgets.QWidget):
    pass


class LoginForm(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.email_field = QtWidgets.QLineEdit(self)
        self.password_field = QtWidgets.QLineEdit(self)
        self.password_field.setEchoMode(QtWidgets.QLineEdit.Password)

        self.login_button = QtWidgets.QPushButton("Log in")
        self.login_button.clicked.connect(self.button_clicked)

        main_form = QtWidgets.QFormLayout()
        main_form.addWidget(QtWidgets.QLabel("Enter your login information to continue."))
        main_form.addRow("Email", self.email_field)
        main_form.addRow("Password", self.password_field)
        main_form.addWidget(self.login_button)

        self.setLayout(main_form)
        self.show()

        self.resize(384, self.height())

    def email(self):
        return self.email_field.text()

    def password(self):
        return self.password_field.text()

    def button_clicked(self):
        self.close()

class FaceRetrieverThread(QtCore.QThread):
    retrieved = QtCore.pyqtSignal(QtGui.QIcon)

    def __init__(self, username):
        super().__init__()
        self.username = username

    def run(self):
        img = requests.get("https://minotar.net/avatar/" + self.username + "/32.png")
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(img.content)
        self.retrieved.emit(QtGui.QIcon(pixmap))

class FetchString(QtCore.QThread):
    fetched = QtCore.pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        resp = requests.get(self.url).text
        self.fetched.emit(resp)