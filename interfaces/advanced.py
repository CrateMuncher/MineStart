import json
import threading

from PySide import QtCore, QtGui
import requests

import launcher


class MineStartAdvanced(QtGui.QMainWindow):
    change_to_basic = QtCore.Signal()

    def __init__(self):
        super(MineStartAdvanced, self).__init__()

        self.launcher = launcher.Launcher()
        self.launcher.get_available_versions()  # Just to get the cache up

        logged_in = len(self.launcher.user_accounts) > 0
        while not logged_in:
            try:
                form = LoginForm()
                form.exec_()
                self.launcher.authenticate_password(form.email(), form.password())
                logged_in = True
            except launcher.InvalidCredentialsError:
                pass

        self.main_widget = QtGui.QWidget()

        self.toolbar = QtGui.QToolBar()
        self.toolbar.addAction(QtGui.QIcon("assets/icons/user_add.png"), "Add Profile")
        self.toolbar.addAction(QtGui.QIcon("assets/icons/user_delete.png"), "Remove Profile")
        self.play_button = self.toolbar.addAction(QtGui.QIcon("assets/icons/play.png"), "Play Game")
        self.play_button.triggered.connect(self.launch)
        self.settings_button = self.toolbar.addAction(QtGui.QIcon("assets/icons/settings.png"), "Profile Options")

        self.player_chooser = QtGui.QComboBox()
        self.player_chooser.setIconSize(QtCore.QSize(32, 32))
        self.face_thread = {}
        for number, user_account in enumerate(self.launcher.user_accounts.itervalues()):
            self.player_chooser.insertItem(number, user_account.username)

            def apply_face(image):
                pixmap = QtGui.QPixmap.fromImage(image)
                self.player_chooser.setItemIcon(number, QtGui.QIcon(pixmap))

            self.player_chooser.setItemIcon(number, QtGui.QIcon("assets/profile_icons/steve.png"))

            face_retriever = FaceRetrieverThread(user_account.username)
            face_retriever.retrieved.connect(apply_face)
            face_retriever.start()

            self.face_thread[user_account.username] = face_retriever # To make it not garbage collect

        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(self.toolbar)
        self.removeToolBarBreak(self.toolbar)

        self.profiles = QtGui.QListWidget(self.main_widget)
        self.profiles.setObjectName("AdvancedProfileList")
        self.profiles.setViewMode(QtGui.QListView.IconMode)
        self.profiles.setMovement(QtGui.QListView.Static)
        self.profiles.setIconSize(QtCore.QSize(64, 64))
        self.profiles.customContextMenuRequested.connect(self.open_profile_context_menu)
        self.profiles.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.launching = False

        for profile in self.launcher.profiles.itervalues():
            item = QtGui.QListWidgetItem(QtGui.QIcon("assets/profile_icons/grass.png"), profile.name)
            self.profiles.addItem(item)
            if profile == self.launcher.current_profile:
                item.setSelected(True)

        self.status_up_pixmap = QtGui.QPixmap("assets/lamp/redstone_lamp_on.png")
        self.status_down_pixmap = QtGui.QPixmap("assets/lamp/redstone_lamp_off.png")

        self.uptime_skins = QtGui.QLabel()
        self.uptime_session = QtGui.QLabel()
        self.uptime_website = QtGui.QLabel()
        self.uptime_realms = QtGui.QLabel()
        self.uptime_login = QtGui.QLabel()
        self.uptime_text = QtGui.QLabel()
        self.refresh_status()

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)

        # self.launch_button = QtGui.QPushButton("Launch Minecraft!", self.main_widget)
        # self.launch_button.setObjectName("AdvancedLaunchButton")

        top_hbox = QtGui.QHBoxLayout()

        bottom_hbox = QtGui.QHBoxLayout()

        bottom_hbox.addWidget(self.uptime_skins)
        bottom_hbox.addWidget(self.uptime_session)
        bottom_hbox.addWidget(self.uptime_website)
        bottom_hbox.addWidget(self.uptime_realms)
        bottom_hbox.addWidget(self.uptime_login)
        bottom_hbox.addWidget(self.uptime_text)
        bottom_hbox.addStretch(1)
        bottom_hbox.addWidget(QtGui.QLabel("Welcome,"))
        bottom_hbox.addWidget(self.player_chooser)

        main_vbox = QtGui.QVBoxLayout()
        main_vbox.addLayout(top_hbox)
        main_vbox.addWidget(self.profiles)
        main_vbox.addLayout(bottom_hbox)

        self.main_widget.setLayout(main_vbox)
        self.setCentralWidget(self.main_widget)
        self.resize(854, 480)
        self.show()

    def open_settings(self, profile):
        dialog = Settings(profile, self.launcher, self)

    def launch(self):
        if self.launching:
            return
        self.launching = True
        for profile in self.launcher.profiles.itervalues():
            if self.profiles.currentItem().text() == profile.name:
                self.launcher.current_profile = profile

        self.launcher_popup = QtGui.QWidget()

        status_label = QtGui.QListWidget(self.launcher_popup)
        close_button = QtGui.QPushButton("Cancel", self.launcher_popup)
        main_vbox = QtGui.QVBoxLayout()
        main_vbox.addWidget(status_label)
        main_vbox.addWidget(close_button)

        self.launcher_popup.setLayout(main_vbox)
        self.launcher_popup.resize(480, 320)
        self.launcher_popup.show()

        def close_window():
            self.launcher_popup.close()

        def message(string):
            status_label.addItem(QtGui.QListWidgetItem(string))
            status_label.scrollToBottom()

        def launched():
            self.launching = False

        self.launch_thread = LauncherThread(self.launcher, self.player_chooser.currentText())
        self.launch_thread.message.connect(message)
        self.launch_thread.finished.connect(close_window)
        self.launch_thread.launched.connect(launched)
        self.launch_thread.start()

    def open_profile_context_menu(self, pos):
        def settings():
            for profile in self.launcher.profiles.itervalues():
                if profile.name == item.text():
                    self.open_settings(profile)

        item = self.profiles.itemAt(pos)
        if item is not None:
            global_pos = self.profiles.mapToGlobal(pos)

            menu = QtGui.QMenu()

            settings_ac = menu.addAction("Settings")
            settings_ac.triggered.connect(settings)

            menu.exec_(global_pos)

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

class Settings(QtGui.QDialog):
    def __init__(self, profile, launcher_, parent=None):
        super(Settings, self).__init__(parent)
        self.profile = profile
        self.launcher = launcher_

        self.tabs = QtGui.QTabWidget()

        self.general_tab = QtGui.QWidget()

        self.version_selector = QtGui.QListWidget()
        latest_snapshot = QtGui.QListWidgetItem("Latest Snapshot")
        latest_release = QtGui.QListWidgetItem("Latest Release")
        self.version_selector.addItem(latest_snapshot)
        self.version_selector.addItem(latest_release)

        if self.profile.version == "latestsnapshot":
            latest_snapshot.setSelected(True)
        elif self.profile.version == "latestrelease":
            latest_release.setSelected(True)

        self.version_selector.currentItemChanged.connect(self.update_current_version)

        for version in self.launcher.get_available_versions():
            item = QtGui.QListWidgetItem(version)
            self.version_selector.addItem(item)
            if version == self.profile.version:
                item.setSelected(True)

        self.resolution_w = QtGui.QSpinBox()
        self.resolution_w.setMaximum(9999)
        self.resolution_w.setValue(int(self.profile.resolution.split("x")[0]))
        self.resolution_w.valueChanged.connect(self.update_resolution)
        self.resolution_h = QtGui.QSpinBox()
        self.resolution_h.setMaximum(9999)
        self.resolution_h.setValue(int(self.profile.resolution.split("x")[1]))
        self.resolution_h.valueChanged.connect(self.update_resolution)


        resolution_hbox = QtGui.QHBoxLayout()
        resolution_hbox.addWidget(self.resolution_w)
        resolution_hbox.addWidget(QtGui.QLabel("x"))
        resolution_hbox.addWidget(self.resolution_h)
        resolution_hbox.addStretch(1)

        general_form = QtGui.QFormLayout()
        general_form.addRow("Version", self.version_selector)
        general_form.addRow("Resolution", resolution_hbox)

        self.general_tab.setLayout(general_form)
        self.tabs.addTab(self.general_tab, "General")

        main_vbox = QtGui.QVBoxLayout()
        main_vbox.addWidget(self.tabs)

        self.setLayout(main_vbox)
        self.resize(320, 240)
        self.show()

    def update_current_version(self):
        if self.version_selector.currentItem().text() == "Latest Snapshot":
            self.profile.version = "latestsnapshot"
        elif self.version_selector.currentItem().text() == "Latest Release":
            self.profile.version = "latestrelease"
        else:
            self.profile.version = self.version_selector.currentItem().text()
        self.launcher.save_config()

    def update_resolution(self):
        res = str(self.resolution_w.value()) + "x" + str(self.resolution_h.value())
        self.profile.resolution = res
        self.launcher.save_config()

class LoginForm(QtGui.QDialog):
    def __init__(self):
        super(LoginForm, self).__init__()

        self.email_field = QtGui.QLineEdit(self)
        self.password_field = QtGui.QLineEdit(self)
        self.password_field.setEchoMode(QtGui.QLineEdit.Password)

        self.login_button = QtGui.QPushButton("Log in")
        self.login_button.clicked.connect(self.button_clicked)

        main_form = QtGui.QFormLayout()
        main_form.addWidget(QtGui.QLabel("Enter your login information to continue."))
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
    retrieved = QtCore.Signal(QtGui.QImage)

    def __init__(self, username):
        super(FaceRetrieverThread, self).__init__()
        self.username = username

    def run(self):
        img = requests.get("https://minotar.net/avatar/" + self.username + "/32.png")
        image = QtGui.QImage()
        image.loadFromData(img.content)
        self.retrieved.emit(image)

class FetchString(QtCore.QThread):
    fetched = QtCore.Signal(str)

    def __init__(self, url):
        super(FetchString, self).__init__()
        self.url = url

    def run(self):
        resp = requests.get(self.url).text
        self.fetched.emit(resp)

class LauncherThread(QtCore.QThread):
    launched = QtCore.Signal()
    message = QtCore.Signal(str)
    finished = QtCore.Signal()

    def __init__(self, launcher, user_account):
        super(LauncherThread, self).__init__()
        self.launcher = launcher
        self.user_account = user_account

    def run(self):
        def message(string):
            self.message.emit(string)

        def launched():
            self.launched.emit()
        self.launcher.status = message
        self.launcher.launched = launched

        self.launcher.launch(self.launcher.get_user_account_by_name(self.user_account))
        self.finished.emit()
