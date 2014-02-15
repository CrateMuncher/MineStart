import glob
import json
import os
import random
import string
import subprocess
import sys
import zipfile

import requests

from recordtype import recordtype
import utils


class Launcher(object):
    def __init__(self):
        self.available_versions = []
        self.debug = self.log_to_console  # A method taking one positional argument (the message)
        self.status = self.log_info  # A method taking one positional argument (the message)
        self.current_profile = None
        self.client_token = None
        self.profiles = {}
        self.user_accounts = {}

        data_dir = get_data_folder()
        self.config = utils.Config(os.path.join(data_dir, "config.json"), defaults={
            "client_token": ''.join(
                random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(32)),
            "current_profile": "Minecraft",
            "profiles": {
            },
            "user_accounts": {}
        })

        self.load_config()
        self.save_config()  # Create all the stuff

    def log_to_console(self, message, type="normal"):
        pass
        # print("[" + type.upper() + "] " + message)

    def get_available_versions(self):
        if len(self.available_versions) <= 0:
            json = requests.get("https://s3.amazonaws.com/Minecraft.Download/versions/versions.json").json()
            self.available_versions = [version["id"] for version in json["versions"]]
            return self.available_versions
        else:
            return self.available_versions

    def log_info(self, message):
        print(message)

    def load_config(self):
        if len(self.config["profiles"]) == 0:
            self.config["profiles"] = {
                "Minecraft": {
                    "mods": [],
                    "name": "Minecraft",
                    "resolution": "854x480",
                    "version": "latestrelease"
                }
            }

        profiles = self.config["profiles"]
        for profile in profiles.itervalues():
            self.profiles[profile["name"]] = Profile.deserialize(profile)

        # Get the current profile as specified by the config
        # If it doesn't specify any profile name, use "Minecraft"
        # If THAT doesn't exist, use the first profile
        self.current_profile = self.profiles.get(self.config["current_profile"])
        self.debug("Default profile: " + self.current_profile.name)

        self.client_token = self.config["client_token"]
        json_user_accounts = self.config["user_accounts"]
        for name, account in json_user_accounts.iteritems():
            self.user_accounts[name] = UserAccount.deserialize(account)

        self.save_config()

    def save_config(self):
        self.debug("Saving config...")

        self.config["client_token"] = self.client_token
        self.config["current_profile"] = self.current_profile.name

        self.config["profiles"] = {}
        for name, profile in self.profiles.iteritems():
            self.config["profiles"][name] = profile.serialize()

        self.config["user_accounts"] = {}
        for name, account in self.user_accounts.iteritems():
            self.config["user_accounts"][name] = account.serialize()

        self.config.save()


    def launch(self, user_account):
        self.debug("Launching game!")
        self.status("Starting game...")
        data_dir = get_data_folder()
        version = self.current_profile.get_version_name()

        version_info = requests.get(
            "https://s3.amazonaws.com/Minecraft.Download/versions/" + version + "/" + version + ".json").json()

        version_dir = os.path.join(data_dir, os.path.join("profiles", self.current_profile.name))
        assets_dir = os.path.join(version_dir, "assets")
        lib_dir = os.path.join(version_dir, "libraries")
        game_dir = os.path.join(version_dir, "game")
        natives_dir = os.path.join(version_dir, "natives")
        if not os.path.exists(assets_dir):
            self.download_assets(version, assets_dir)
        if not os.path.exists(lib_dir):
            self.download_libraries(version, lib_dir, natives_dir)
        if not os.path.exists(game_dir):
            self.download_game(version, game_dir)

        classpath = []
        for file in glob.glob(os.path.join(lib_dir, "*.jar")):
            classpath.append(file)
        classpath.append(os.path.join(game_dir, version + ".jar"))

        cp_seperator = ":"
        if get_current_os() == "windows":
            cp_seperator = ";"

        args = []
        if get_current_os() == "windows":
            args.append("-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump")
        elif get_current_os() == "osx":
            args.append("-Xdock:icon=" + os.path.join(assets_dir, os.path.join("icons", "minecraft.icns")))
            args.append("-Xdock:name=Minecraft")

        args.append("-Djava.library.path={0}".format(natives_dir + os.sep))
        args.append("-cp {0}".format(cp_seperator.join(classpath)))
        args.append(version_info["mainClass"])
        args.append(version_info["minecraftArguments"].replace("${auth_player_name}", user_account.username).replace(
            "${version_name}", version).replace("${game_directory}", game_dir).replace(
            "${assets_root}", assets_dir).replace("${assets_index_name}", version_info.get("assets", "legacy")).replace(
            "${auth_uuid}", user_account.uuid).replace("${auth_access_token}", user_account.access_token).replace(
            "${user_properties}", "{}").replace("${user_type}", "whatdoesthismean"))
        args.append("--width {0}".format(self.current_profile.resolution.split("x")[0]))
        args.append("--height {0}".format(self.current_profile.resolution.split("x")[1]))

        command = "\"" + get_javaw_path() + "\" " + " ".join(args)
        self.debug("Running Minecraft using command: " + command)
        popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.status("Minecraft started!")
        while True:
            self.status(str(popen.stdout.readline()))

    def download_game(self, version, game_dir):
        self.debug("Downloading game jar...")
        self.status("Downloading game code...")
        try:
            os.makedirs(game_dir)
        except OSError:
            pass
        filename = os.path.join(game_dir, version + ".jar")
        url = "https://s3.amazonaws.com/Minecraft.Download/versions/" + version + "/" + version + ".jar"
        r = requests.get(url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

    def download_libraries(self, version, lib_dir, extract_dir):
        self.debug("Downloading libraries...")
        try:
            os.makedirs(lib_dir)
        except OSError:
            pass

        try:
            os.makedirs(extract_dir)
        except OSError:
            pass
        version_info = requests.get(
            "https://s3.amazonaws.com/Minecraft.Download/versions/" + version + "/" + version + ".json").json()

        library_count = len(version_info["libraries"])
        library_current = 0
        for library in version_info["libraries"]:
            library_current += 1
            self.status("Downloading libraries [" + str(library_current) + "/" + str(library_count) + "]")
            library_name = library["name"]
            self.debug("Found library " + library_name)
            if self.can_use_library(library):
                native = None
                if "natives" in library:
                    native = library["natives"].get(get_current_os(), None)
                base_dir = library_name.split(":")[0].replace(".", "/") + "/" + library_name.split(":")[1] + "/" + \
                           library_name.split(":")[2]
                path = base_dir
                if native is not None:
                    path = base_dir
                    remote_filename = library_name.split(":")[1] + "-" + library_name.split(":")[
                        2] + "-" + native + ".jar"
                else:
                    remote_filename = library_name.split(":")[1] + "-" + library_name.split(":")[2] + ".jar"
                url = "https://libraries.minecraft.net/" + path + "/" + remote_filename
                url = url.replace("${arch}", str(get_arch()))
                filename = os.path.join(lib_dir, remote_filename)
                self.debug("Downloading library at " + url)
                r = requests.get(url, stream=True)
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            f.flush()

                if "extract" in library:
                    with zipfile.ZipFile(filename) as zip:
                        names = zip.namelist()

                        for name in names:
                            excluded = False
                            for exclusion in library["extract"]["exclude"]:
                                if name.startswith(exclusion):
                                    excluded = True

                            if not excluded:
                                zip.extract(name, path=extract_dir)

    def download_assets(self, version, assets_dir):
        self.debug("Downloading assets...")
        try:
            os.makedirs(assets_dir)
        except OSError:
            pass
        version_info = requests.get(
            "https://s3.amazonaws.com/Minecraft.Download/versions/" + version + "/" + version + ".json").json()

        index_name = version_info.get("assets", None)
        if index_name is None:
            index_name = "legacy"
        self.index_name = index_name
        self.debug("Index name: ", index_name)

        indexes_resp = requests.get("https://s3.amazonaws.com/Minecraft.Download/indexes/" + index_name + ".json")
        indexes = indexes_resp.json()
        try:
            os.makedirs(os.path.join(assets_dir, "indexes"))
        except OSError:
            pass
        with open(os.path.join(assets_dir, "indexes", index_name + ".json"), "w+") as f:
            f.writelines(indexes_resp.text)

        assets_count = len(indexes["objects"].iteritems())
        assets_current = 0

        for path, obj in indexes["objects"].iteritems():
            assets_current += 1
            self.status("Downloading assets [" + str(assets_current) + "/" + str(assets_count) + "]")
            self.debug("Found object at " + path)
            if index_name == "legacy":
                filename = os.path.join(assets_dir, "virtual", index_name, path)
            else:
                filename = os.path.join(assets_dir, "objects", obj["hash"][0:2], obj["hash"])
            if os.sep in filename:
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError:
                    pass
            url = "http://resources.download.minecraft.net/" + obj["hash"][0:2] + "/" + obj["hash"]
            self.debug("Downloading object at " + url)
            r = requests.get(url, stream=True)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()

    def can_use_library(self, library_json):
        if not "rules" in library_json:
            return True
        else:
            can_use = True
            for rule in library_json["rules"]:
                if "os" in rule:
                    os = rule["os"]["name"]
                    if get_current_os() == os:
                        if rule["action"] == "allow":
                            can_use = True
                        else:
                            can_use = False
            return can_use

    def get_user_account_by_name(self, name):
        return self.user_accounts.get(name, None)

    def get_user_account_by_id(self, id_):
        for account in self.user_accounts.itervalues():
            if account.uuid == id_:
                return account

    def sign_all_out(self):
        for account in self.user_accounts.itervalues():
            account.sign_out(self.client_token)

    def is_user_logged_in(self, user_data):
        pass

    def authenticate_password(self, username, password):
        self.status("Authenticating...")
        data = {
            "agent": {
                "name": "Minecraft",
                "version": "1"
            },
            "selectedProfile": None,
            "username": username,
            "password": password,
            "clientToken": self.client_token
        }
        headers = {'Content-type': 'application/json'}
        r = requests.post("https://authserver.mojang.com/authenticate", headers=headers, data=json.dumps(data))
        resp = r.json()
        if "error" in resp and resp["error"] == "ForbiddenOperationException":
            self.status("Error: Invalid username or password!")
            raise InvalidCredentialsError("Error: Invalid username or password!")
        self.user_accounts = {}
        for new_profile in resp["availableProfiles"]:
            account = UserAccount(username=new_profile["name"], uuid=new_profile["id"], access_token=None)
            self.user_accounts[account.username] = account
        selected_account = self.get_user_account_by_id(resp["selectedProfile"]["id"])
        selected_account.access_token = resp["accessToken"]
        self.save_config()


class Profile(recordtype('Profile', ["name", "version", "mods", "resolution"])):
    def get_version_name(self):
        json = requests.get("https://s3.amazonaws.com/Minecraft.Download/versions/versions.json").json()
        if self.version == "latestsnapshot":
            return json["latest"]["snapshot"]
        elif self.version == "latestrelease":
            return json["latest"]["release"]
        else:
            for version in json["versions"]:
                if version["id"] == self.version:
                    return version["id"]

    def apply_mods(self, original_jar, new_jar):
        def mod_priority(mod):
            return mod.priority

        sorted_mods = sorted(self.mods, key=mod_priority, reverse=True)
        for mod in sorted_mods:
            pass

    def serialize(self):
        return {
            "name": self.name,
            "version": self.version,
            "mods": [mod.serialize() for mod in self.mods],
            "resolution": self.resolution
        }

    @staticmethod
    def deserialize(data):
        return Profile(name=data["name"], version=data["version"],
                       mods=[Mod.deserialize(mod_data) for mod_data in data["mods"]], resolution=data["resolution"])


class Mod(recordtype('Mod', ['path', 'priority'])):
    def serialize(self):
        return {
            "path": self.path,
            "priority": self.priority
        }

    @staticmethod
    def deserialize(data):
        return Mod(path=data["path"], priority=data["priority"])


class UserAccount(recordtype('UserAccount', ["username", "uuid", "access_token"])):
    def is_logged_in(self, launcher):
        if self.access_token is None:
            return False
        if self.access_token == "":
            return False

        data = {
            "accessToken": self.access_token,
            "clientToken": launcher.client_token
        }
        headers = {'Content-type': 'application/json'}
        r = requests.post("https://authserver.mojang.com/refresh", headers=headers, data=json.dumps(data))
        resp = r.json()
        if "error" in resp and resp["error"] == "ForbiddenOperationException":
            return False
        if "accessToken" in resp:
            self.access_token = resp["accessToken"]
            return True
        else:
            return False

    def relogin(self, launcher):
        launcher.status("Authenticating...")
        data = {
            "agent": {
                "name": "Minecraft",
                "version": "1"
            },
            "accessToken": self.access_token,
            "clientToken": launcher.client_token
        }
        headers = {'Content-type': 'application/json'}
        r = requests.post("https://authserver.mojang.com/refresh", headers=headers, data=json.dumps(data))
        resp = r.json()
        if "error" in resp and (
                        resp["error"] == "ForbiddenOperationException" or resp["error"] == "IllegalArgumentException"):
            launcher.status("Error: Invalid session key!")
            raise InvalidCredentialsError("Error: Invalid session key!")
        self.access_token = resp["accessToken"]
        launcher.save_config()
        launcher.status("Authenticated")

    def sign_out(self, client_token):
        data = {
            "accessToken": self.access_token,
            "clientToken": client_token
        }
        headers = {'Content-type': 'application/json'}
        requests.post("https://authserver.mojang.com/invalidate", headers=headers, data=json.dumps(data))
        self.access_token = None

    def serialize(self):
        return {
            "username": self.username,
            "uuid": self.uuid,
            "access_token": self.access_token
        }

    @staticmethod
    def deserialize(data):
        return UserAccount(username=data["username"], uuid=data["uuid"], access_token=data["access_token"])


class LauncherError(Exception):
    pass


class InvalidCredentialsError(LauncherError):
    pass


def get_data_folder():
    APPNAME = "MineStart"
    import sys
    from os import path, environ

    if sys.platform == 'darwin':
        from AppKit import NSSearchPathForDirectoriesInDomains
        # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
        # NSApplicationSupportDirectory = 14
        # NSUserDomainMask = 1
        # True for expanding the tilde into a fully qualified path
        appdata = path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
    elif sys.platform == 'win32':
        appdata = path.join(environ['APPDATA'], APPNAME)
    else:
        appdata = path.expanduser(path.join("~", "." + APPNAME))
    return appdata


def get_current_os():
    platform = sys.platform
    if platform == 'darwin':
        return "osx"
    elif sys.platform == 'win32':
        return "windows"
    else:
        return "linux"


def get_javaw_path():
    if "JAVA_HOME" in os.environ:
        j_home = os.environ["JAVA_HOME"]
        j_home = "C:\Program Files (x86)\Java\jre7"

        bin = os.path.join(j_home, "bin")
        if os.path.exists(bin):
            java = os.path.join(bin, "java")
            javaw = os.path.join(bin, "javaw")
            if check_java("\"" + java + "\""):
                return javaw

    if check_java("java"):
        return "javaw"


def check_java(path):
    popen = subprocess.Popen(path + " -version", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ver_string = popen.stderr.readlines()
    return "Java(TM)" in str(ver_string[1])


def get_arch():
    import struct

    return 8 * struct.calcsize("P")