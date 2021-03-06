import json
import threading

from PySide import QtGui, QtGui, QtCore
import requests

import launcher


class MineStartBasic(QtGui.QMainWindow):
    change_to_advanced = QtCore.Signal()

    def __init__(self):
        super(MineStartBasic, self).__init__()
        self.logged_in_users = []
        self.launcher = launcher.Launcher()
        self.launcher.status = self.status_log
        self.launcher.debug = self.debug_log

        self.main_widget = QtGui.QWidget(self)
        self.main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(self.popup_context)
        self.main_widget.setObjectName("BasicMainWidget")
        self.mojang = QtGui.QLabel(self.main_widget)
        self.mojang.setPixmap(QtGui.QPixmap("assets/misc/mojang-small.png"))

        self.version = QtGui.QLabel(self.main_widget)
        self.version.setText(
            self.launcher.current_profile.name + " [" + self.launcher.current_profile.get_version_name() + "]")

        self.status = QtGui.QLabel(self.main_widget)
        self.status.setObjectName("StatusLine")
        self.status.setAlignment(QtCore.Qt.AlignCenter)

        self.minecraft = QtGui.QLabel(self.main_widget)
        self.minecraft.setAlignment(QtCore.Qt.AlignCenter)
        self.minecraft.setPixmap(QtGui.QPixmap("assets/misc/logo.png"))

        self.close_btn = QtGui.QPushButton(self.main_widget)
        self.close_btn.setFlat(True)
        self.close_btn.setIcon(QtGui.QIcon(QtGui.QPixmap("assets/icons/close.png").scaled(QtCore.QSize(32, 32))))
        self.close_btn.clicked.connect(self.close)

        self.login_panel = LoginPanel(self.main_widget)
        self.login_panel.login_started.connect(self.login)

        self.user_selector = QtGui.QComboBox(self.main_widget)
        self.refresh_user_selector()
        self.user_selector.currentIndexChanged.connect(self.changed_user)

        self.launcher_panel = LauncherPanel(self.main_widget)
        self.launcher_panel.game_started.connect(self.launch)
        self.launcher_panel.user_signed_out.connect(self.sign_out)
        self.launcher_panel.settings_opened.connect(self.settings)

        self.status_up_pixmap = QtGui.QPixmap("assets/lamp/redstone_lamp_on.png")
        self.status_down_pixmap = QtGui.QPixmap("assets/lamp/redstone_lamp_off.png")

        self.uptime_skins = QtGui.QLabel()
        self.uptime_session = QtGui.QLabel()
        self.uptime_website = QtGui.QLabel()
        self.uptime_realms = QtGui.QLabel()
        self.uptime_login = QtGui.QLabel()
        self.refresh_status()

        self.panels = QtGui.QStackedLayout()
        self.panels.addWidget(self.login_panel)
        self.panels.addWidget(self.launcher_panel)
        self.panels.setCurrentIndex(0)

        top_hbox = QtGui.QHBoxLayout()
        top_hbox.addWidget(self.mojang)
        top_hbox.addStretch(1)
        top_hbox.addWidget(self.close_btn)

        centered_vbox = QtGui.QVBoxLayout()
        centered_vbox.addWidget(self.minecraft)
        centered_vbox.addWidget(self.user_selector)
        centered_vbox.addLayout(self.panels)
        centered_vbox.addWidget(self.status)

        middle_hbox = QtGui.QHBoxLayout()
        middle_hbox.addStretch(1)
        middle_hbox.addLayout(centered_vbox)
        middle_hbox.addStretch(1)

        uptime_hbox = QtGui.QHBoxLayout()
        uptime_hbox.addStretch(1)
        uptime_hbox.addWidget(self.uptime_skins)
        uptime_hbox.addWidget(self.uptime_session)
        uptime_hbox.addWidget(self.uptime_website)
        uptime_hbox.addWidget(self.uptime_realms)
        uptime_hbox.addWidget(self.uptime_login)
        uptime_hbox.addStretch(1)

        bottom_hbox = QtGui.QHBoxLayout()
        bottom_hbox.addWidget(self.version, 1)
        bottom_hbox.addLayout(uptime_hbox, 1)
        bottom_hbox.addStretch(1)

        main_vbox = QtGui.QVBoxLayout()
        main_vbox.addLayout(top_hbox)
        main_vbox.addStretch(1)
        main_vbox.addLayout(middle_hbox)
        main_vbox.addStretch(1)
        main_vbox.addLayout(bottom_hbox)

        self.main_widget.setLayout(main_vbox)
        self.setCentralWidget(self.main_widget)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.show()
        self.resize(854, 480)
        self.setObjectName("BasicMainWindow")
        self.move(QtGui.QApplication.desktop().screen().rect().center() - self.rect().center())

        self.refresh_logged_in()
        self.changed_user()

        self.status_timer = QtCore.QTimer(self)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(5000)

    def status_log(self, msg):
        self.status.setText(msg)

    def debug_log(self, msg):
        print(msg)

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

        self.refresh_thread = FetchString("http://xpaw.ru/mcstatus/status.json")
        self.refresh_thread.fetched.connect(update_ui)
        self.refresh_thread.start()

    def login(self):
        try:
            self.launcher.authenticate_password(self.login_panel.username(), self.login_panel.password())
            self.panels.setCurrentIndex(1)
            self.refresh_logged_in()
            self.refresh_user_selector()
            self.status.setText("Authenticated!")
        except launcher.InvalidCredentialsError:
            self.status.setText("Invalid username or password!")
            return

    def changed_user(self):
        if self.user_selector.currentText() in self.logged_in_users:
            self.panels.setCurrentIndex(1)
        else:
            self.panels.setCurrentIndex(0)

    def refresh_logged_in(self):
        self.logged_in_users = []
        for user in self.launcher.user_accounts.itervalues():
            try:
                user.relogin(self.launcher)
                self.logged_in_users.append(user.username)
            except launcher.InvalidCredentialsError:
                pass

    def refresh_user_selector(self):
        if len(self.launcher.user_accounts) <= 1:
            self.user_selector.hide()
        else:
            self.user_selector.show()
        for profile in self.launcher.user_accounts.iterkeys():
            self.user_selector.addItem(profile)

    def launch(self):
        def async():
            self.launcher.launch(self.launcher.get_user_account_by_name(self.user_selector.currentText()))

        thread = threading.Thread(target=async)
        thread.start()

    def sign_out(self):
        current_user = self.launcher.get_user_account_by_name(self.user_selector.currentText())
        current_user.sign_out(self.launcher.client_token)
        self.logged_in_users.remove(current_user.username)
        self.panels.setCurrentIndex(0)

    def settings(self):
        settings_menu = Settings(self.launcher)
        settings_menu.exec_()
        self.version.setText(
            self.launcher.current_profile.name + " [" + self.launcher.current_profile.get_version_name() + "]")

    def popup_context(self, pos):
        position = self.main_widget.mapToGlobal(pos)

        def change_advanced():
            self.change_to_advanced.emit()

        self.menu = QtGui.QMenu()

        change_to_advanced = self.menu.addAction("Change to Advanced mode...")
        change_to_advanced.triggered.connect(change_advanced)

        self.menu.popup(position)

    def mousePressEvent(self, event):
        # This makes the window draggable
        if event.button() == QtCore.Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        # This makes the window draggable
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()


class LoginPanel(QtGui.QWidget):
    login_started = QtCore.Signal()

    def __init__(self, parent=None):
        super(LoginPanel, self).__init__(parent)
        self.setObjectName("BasicLauncherPanel")

        self.username_box = QtGui.QLineEdit()
        self.username_box.setPlaceholderText("Email")

        self.password_box = QtGui.QLineEdit()
        self.password_box.setEchoMode(QtGui.QLineEdit.Password)
        self.password_box.setPlaceholderText("Password")

        self.login_button = QtGui.QPushButton("Log In")
        self.login_button.clicked.connect(self.login_clicked)

        main_form = QtGui.QVBoxLayout()
        main_form.addWidget(self.username_box)
        main_form.addWidget(self.password_box)
        main_form.addWidget(self.login_button)

        self.setMinimumWidth(384)

        self.setLayout(main_form)

    def username(self):
        return self.username_box.text()

    def password(self):
        return self.password_box.text()

    def setUsername(self, username):
        self.username_box.setText(username)

    def setPassword(self, password):
        self.password_box.setText(password)

    def login_clicked(self):
        self.login_started.emit()


class LauncherPanel(QtGui.QWidget):
    game_started = QtCore.Signal()
    user_signed_out = QtCore.Signal()
    settings_opened = QtCore.Signal()

    def __init__(self, parent=None):
        super(LauncherPanel, self).__init__(parent)
        self.setObjectName("BasicLauncherPanel")

        self.launch_button = QtGui.QPushButton("Launch", self)
        self.launch_button.clicked.connect(self.launch_clicked)

        self.settings_button = QtGui.QPushButton("Settings", self)
        self.settings_button.clicked.connect(self.settings_clicked)

        self.signout_button = QtGui.QPushButton("Sign Out", self)
        self.signout_button.clicked.connect(self.signout_clicked)

        secondary = QtGui.QHBoxLayout()
        secondary.addWidget(self.settings_button)
        secondary.addWidget(self.signout_button)

        main_form = QtGui.QVBoxLayout()
        main_form.addWidget(self.launch_button)
        main_form.addLayout(secondary)

        self.setMinimumWidth(384)

        self.setLayout(main_form)

    def launch_clicked(self):
        self.game_started.emit()

    def signout_clicked(self):
        self.user_signed_out.emit()

    def settings_clicked(self):
        self.settings_opened.emit()


class Settings(QtGui.QDialog):
    def __init__(self, launcher):
        super(Settings, self).__init__()
        self.updating = False
        self.launcher = launcher

        self.general_tab = QtGui.QWidget(self)
        self.tabs = QtGui.QTabWidget(self)
        self.tabs.addTab(self.general_tab, "General")

        self.general_version = QtGui.QListWidget(self.general_tab)

        self.general_resolution_w = QtGui.QSpinBox(self.general_tab)
        self.general_resolution_w.setMaximum(9999)
        self.general_resolution_x = QtGui.QLabel("x", self.general_tab)
        self.general_resolution_h = QtGui.QSpinBox(self.general_tab)
        self.general_resolution_h.setMaximum(9999)

        self.save_button = QtGui.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        resolution_hbox = QtGui.QHBoxLayout()
        resolution_hbox.addWidget(self.general_resolution_w)
        resolution_hbox.addWidget(self.general_resolution_x)
        resolution_hbox.addWidget(self.general_resolution_h)
        resolution_hbox.addStretch(1)

        general_form = QtGui.QFormLayout()
        general_form.addRow("Version", self.general_version)
        general_form.addRow("Resolution", resolution_hbox)

        bottom_hbox = QtGui.QHBoxLayout()
        bottom_hbox.addStretch(1)
        bottom_hbox.addWidget(self.save_button)

        main_vbox = QtGui.QVBoxLayout()
        main_vbox.addWidget(self.tabs)
        main_vbox.addLayout(bottom_hbox)

        self.general_version.currentItemChanged.connect(self.update)
        self.general_resolution_w.valueChanged.connect(self.update)
        self.general_resolution_h.valueChanged.connect(self.update)

        self.general_tab.setLayout(general_form)
        self.setLayout(main_vbox)

        self.fill_in()
        self.save()

    def update(self):
        self.save_button.setEnabled(True)

    def save(self):
        if self.updating:
            return
        self.updating = True
        self.launcher.load_config()
        resolution = str(self.general_resolution_w.value()) + "x" + str(self.general_resolution_h.value())

        current_profile = self.launcher.current_profile
        del self.launcher.profiles[current_profile.name]

        try:
            version = self.general_version.currentItem().text()
            if version == "Latest Release":
                version = "latestrelease"
            elif version == "Latest Snapshot":
                version = "latestsnapshot"
            current_profile.version = version
        except AttributeError:
            pass

        current_profile.resolution = resolution

        self.launcher.current_profile = current_profile
        self.launcher.profiles[current_profile.name] = current_profile

        self.launcher.save_config()
        self.save_button.setEnabled(False)
        self.updating = False

    def fill_in(self):
        if self.updating:
            return
        self.updating = True
        self.launcher.load_config()

        current_profile = self.launcher.current_profile

        version = current_profile.version
        resolution = current_profile.resolution

        self.general_resolution_w.setValue(int(resolution.split("x")[0]))
        self.general_resolution_h.setValue(int(resolution.split("x")[1]))

        versions = self.launcher.get_available_versions()
        latest_snapshot_item = QtGui.QListWidgetItem("Latest Snapshot")
        latest_release_item = QtGui.QListWidgetItem("Latest Release")
        self.general_version.clear()
        self.general_version.addItem(latest_snapshot_item)
        self.general_version.addItem(latest_release_item)
        if version == "latestrelease":
            latest_release_item.setSelected(True)
        elif version == "latestsnapshot":
            latest_snapshot_item.setSelected(True)
        for available_version in versions:
            item = QtGui.QListWidgetItem(available_version)
            self.general_version.addItem(item)
            if version == available_version:
                self.general_version.scrollToItem(item, QtGui.QAbstractItemView.EnsureVisible)
                item.setSelected(True)
        self.launcher.save_config()
        self.updating = False

    def change_current_profile(self):
        for profile in self.launcher.profiles.itervalues():
            if profile.name == self.profile_selector.currentText():
                self.launcher.current_profile = profile
        self.launcher.save_config()
        self.fill_in()

    def add_profile(self):
        self.launcher.load_config()
        new_name = "New Profile"
        count = 1
        while new_name in self.launcher.profiles:
            new_name = "New Profile (" + str(count) + ")"
            count += 1

        new_profile = launcher.Profile(name=new_name, version="latestrelease", mods=[], resolution="854x480")
        self.launcher.profiles[new_name] = new_profile
        self.launcher.current_profile = new_profile
        self.profile_selector.addItem(new_name)
        self.launcher.save_config()

    def del_profile(self):
        self.launcher.load_config()
        if len(self.launcher.profiles) <= 1:
            return
        del self.launcher.profiles[self.profile_selector.currentText()]

        found = False
        i = 0
        while not found:
            if self.profile_selector.itemText(i) == self.profile_selector.currentText():
                self.profile_selector.removeItem(i)
                found = True
            i += 1
        self.launcher.save_config()

class FetchString(QtCore.QThread):
    fetched = QtCore.Signal(str)

    def __init__(self, url):
        super(FetchString, self).__init__()
        self.url = url

    def run(self):
        resp = requests.get(self.url).text
        self.fetched.emit(resp)