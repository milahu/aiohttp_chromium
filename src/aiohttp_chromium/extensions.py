import hashlib
import shutil
import os
import zipfile
import logging
import asyncio



import aiohttp



class ChromiumExtension:

    name = None
    source = None
    session = None
    id = None
    cachedir = None

    def __init__(self, session, pinned=True):

        self.session = session
        self.pinned = pinned

        self._logger = logging.getLogger(self.__class__.__name__)
        self.log = self._logger.debug

        self.cachedir = f"{self.session._extensions_cache_path}/{self.name}"
        self.path = f"{self.session._extensions_path}/{self.name}"

        self.id = get_extension_id(self.path)

        self.settings_cache = f"{self.session._extensions_cache_path}/{self.name}/settings"
        self.settings_path = f"{self.session._chromium_user_data_dir}/Default/Local Extension Settings/{self.id}"

        self.log(f"init done: path: {self.path} id: {self.id}")

    def __await__(self):

        return self.async_init().__await__()

    async def async_init(self):

        if os.path.exists(self.path):
            return

        await self.download()

        await self.unpack()

        await self.fix_path()

        await self.patch()

        await self.load_state()

        self.session._chromium_options.add_argument(f"--load-extension={self.path}")

        if self.pinned:
            self.session._chromium_config["extensions"]["pinned_extensions"].append(self.id)

        self.log(f"async_init done")

        return self

    async def close(self):

        await self.save_state()

        self.log(f"close done")

    async def download(self):

        source_url = self.source["url"]
        source_sha256 = self.source["sha256"]
        source_filename = self.source.get("filename") or os.path.basename(source_url)
        self.cache_filepath = f"{self.cachedir}/{source_filename}"

        os.makedirs(self.cachedir, exist_ok=True)

        if os.path.exists(self.cache_filepath):
            sha256 = sha256sum(self.cache_filepath).hex()
            if sha256 != source_sha256:
                # delete invalid cache file
                print(f"deleting invalid cache file: {self.cache_filepath}. checksum mismatch: {sha256} != {source_sha256}")
                os.unlink(self.cache_filepath)

        if not os.path.exists(self.cache_filepath):
            print(f"downloading {source_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as resp:
                    print(resp.status)
                    #print(await resp.text())
                    with open(self.cache_filepath, 'wb') as fd:
                        chunk_size = 65536
                        async for chunk in resp.content.iter_chunked(chunk_size):
                            fd.write(chunk)

        sha256 = sha256sum(self.cache_filepath).hex()
        if sha256 != source_sha256:
            raise Exception(f"invalid cache file: {self.cache_filepath}. checksum mismatch: {sha256} != {source_sha256}")

    async def unpack(self):

        if self.cache_filepath[-4:].lower() == ".zip":
            with zipfile.ZipFile(self.cache_filepath, "r") as z:
                z.extractall(self.path)
            return

        # TODO extract tar.gz archives

        raise NotImplementedError(f"unpack file {self.cache_filepath}")

    async def fix_path(self):

        # find manifest.json
        # fix self.path
        if os.path.exists(f"{self.path}/manifest.json"):
            return
        path_files = os.listdir(self.path)
        if len(path_files) == 1:
            # no. changing path would change id
            #self.path += "/" + path_files[0]
            os.rename(self.path, self.path + ".tmp")
            os.rename(self.path + ".tmp/" + path_files[0], self.path)
            os.rmdir(self.path + ".tmp")
        if not os.path.exists(f"{self.path}/manifest.json"):
            raise Exception(f"no manifest.json in {self.path}")

    async def patch(self):

        pass

    async def load_state(self):

        if os.path.exists(self.settings_cache):
            self.log(f"load_state: loading settings from {self.settings_cache}")
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            shutil.copytree(self.settings_cache, self.settings_path)

    async def save_state(self):

        if os.path.exists(self.settings_path):
            self.log(f"save_state: saving settings to {self.settings_cache}")
            os.makedirs(os.path.dirname(self.settings_cache), exist_ok=True)
            # FIXME use "rsync" to reduce disk writes
            shutil.copytree(self.settings_path, self.settings_cache)

    async def pre_start(self):

        pass

    async def post_start(self):

        pass



# TODO remove?
def get_settings(path):
    with open(path + "/manifest.json", "r") as f:
        manifest = json.load(f)
    settings = None
    manifest_version = manifest.get("manifest_version", None)
    manifest_permissions = manifest.get("permissions", [])
    manifest_content_scripts = manifest.get("content_scripts", [])
    # list to dict
    # dict(a=1, b=2)
    # dict([["a", 1], ["b", 2]])
    commands = dict(map(lambda key: [key, {"suggested_key": ""}], manifest.get("commands", {}).keys()))
    permissions_scriptable_host = list(itertools.chain.from_iterable(map(lambda s: s["matches"], manifest_content_scripts)))
    permissions_api = list(filter(lambda x: x != "<all_urls>", manifest_permissions))
    permissions_explicit_host = [
        "chrome://favicon/*"
    ] + list(filter(lambda x: x == "<all_urls>", manifest_permissions))
    if manifest_version == 2:
        settings = {
            "path": path,
            "active_permissions": {
                "api": permissions_api,
                "explicit_host": permissions_explicit_host,
                "manifest_permissions": [],
                "scriptable_host": permissions_scriptable_host,
            },
            "commands": commands,
            "content_settings": [],
            # TODO?
            "creation_flags": 38,
            "events": [],
            "first_install_time": "0",
            "from_webstore": False,
            "granted_permissions": {
                "api": permissions_api,
                "explicit_host": permissions_explicit_host,
                "manifest_permissions": [],
                "scriptable_host": permissions_scriptable_host,
            },
            "incognito_content_settings": [],
            "incognito_preferences": {},
            "last_update_time": "0",
            # TODO?
            "location": 4,
            "newAllowFileAccess": True,
            "preferences": {},
            "regular_only_preferences": {},
            # TODO?
            "state": 1,
            "was_installed_by_default": False,
            "was_installed_by_oem": False,
            "withholding_permissions": False
        }
    else:
        raise NotImplementedError(f"manifest version {manifest_version} in chromium extension {path}")
    return settings



import string
def get_extension_id(path: str):
    # FIXME On Windows, the path needs to be encoded as utf-16-le
    # https://stackoverflow.com/questions/26053434
    t = str.maketrans(string.hexdigits[:16], string.ascii_lowercase[:16])
    return hashlib.sha256(path.encode('utf8')).hexdigest()[:32].translate(t)



"""
class EditThisCookie(ChromiumExtension):
    pass
"""



def sha256sum(file_path=None, data=None):
    if data:
        return hashlib.sha256(data).digest()
    assert file_path
    # https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64KB chunks
    hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while data := f.read(BUF_SIZE):
            hash.update(data)
    return hash.digest()
    #print("SHA1: {0}".format(hash.hexdigest()))



import zipfile

class Ublock(ChromiumExtension):

    name = "ublock"
    website = "https://github.com/gorhill/uBlock"
    source = {
        "url": "https://github.com/gorhill/uBlock/releases/download/1.55.0/uBlock0_1.55.0.chromium.zip",
        "sha256": "00cec043e4e30e758a9d8194a018121ac689345fde4d4d02baaac60b954f2d7d",
    }

    async def patch(self):

        self.log(f"patch: patching /js/background.js")
        # TODO refactor patching of files
        with open(self.path + "/js/background.js", "r") as f:
            text = f.read()
        # enable: Suspend network activity until all filter lists are loaded
        text = text.replace(
            "suspendUntilListsAreLoaded: vAPI.Net.canSuspend(),",
            "suspendUntilListsAreLoaded: true,",
        )
        with open(self.path + "/js/background.js", "w") as f:
            f.write(text)

class Buster(ChromiumExtension):

    website = "https://github.com/dessant/buster"
    source_url = "https://github.com/dessant/buster/releases/download/v2.0.1/buster_captcha_solver_for_humans-2.0.1-chrome.zip"
    source_sha256 = "8ebc4833eebfaf04021a534666a9654729245b135a037af71e2e0567b170249e"

    #def add_ublock_chromium_extension(self):
    def __init__(self, session):

        super().__init__()

        raise NotImplementedError

        # old code...

        # add the "buster" extension for captcha solving
        # https://github.com/dessant/buster

        # TODO use self._chromium_extensions dict
        #self._chromium_extensions["buster"] = ...

        # $HOME/.local/opt/buster/buster-client
        self.buster_client_path = f"{self.temp_home}/.local/opt/buster/buster-client"

        # TODO expose option
        #self.buster_client_path = "/nix/store/da5spa9hvs8gbx7pwr3fzalyq8mpvabn-buster-client-0.3.0/opt/buster/buster-client"

        # $HOME/.local/opt/buster/buster-extension
        # this is a non-standard location for the unpacked buster extension
        # unpacked buster_*-chrome.zip from
        # https://github.com/dessant/buster/releases/latest
        self.source_path = f"{self.temp_home}/.local/opt/buster/buster-extension"

        # TODO expose option
        # TODO allow passing a zip file
        self.source_path = os.getcwd() + "/captcha-solver/buster-chrome-2.0.1"

        # copy the unpacked extension to tempdir
        self.path = self.tempdir + "/buster-chrome-extension"
        shutil.copytree(self.source_path, self.path)

        # patch the unpacked extension
        shutil.copy(
            self.path + "/src/background/script.js",
            self.path + "/src/background/script.js.bak"
        )
        background_script_js = None
        with open(self.path + "/src/background/script.js", "r") as f:
            background_script_js = f.read()
        # autoUpdateClientApp: true -> false
        background_script_js = background_script_js.replace("autoUpdateClientApp:!0", "autoUpdateClientApp:!1")
        # navigateWithKeyboard: false -> true
        background_script_js = background_script_js.replace("navigateWithKeyboard:!1", "navigateWithKeyboard:!0")
        # simulateUserInput: false -> true
        background_script_js = background_script_js.replace("simulateUserInput:!1", "simulateUserInput:!0")
        with open(self.path + "/src/background/script.js", "w") as f:
            f.write(background_script_js)
        del background_script_js

        self.id = get_extension_id(self.path)

        # $HOME/.config/chromium/NativeMessagingHosts/org.buster.client.json
        self.buster_native_messaging_host_config = {
            "name": "org.buster.client",
            "description": "Buster",
            "path": self.buster_client_path,
            "type": "stdio",
            "allowed_origins": [
                # fix: Unchecked runtime.lastError: Access to the specified native messaging host is forbidden.
                f"chrome-extension://{self.id}/"
            ]
        }

        # write buster config file
        self.buster_native_messaging_host_path = self._chromium_user_data_dir + "/NativeMessagingHosts/org.buster.client.json"
        logger_print(f"writing buster config file:", self.buster_native_messaging_host_path)
        os.makedirs(self._chromium_user_data_dir + "/NativeMessagingHosts")
        with open(self.buster_native_messaging_host_path, "w") as f:
            json.dump(self.buster_native_messaging_host_config, f, indent=2)

        assert self.session._chromium_config["extensions"]["ui"]["developer_mode"] == True
        self.session._chromium_config["extensions"]["settings"][self.id] = self._chromium_extension_settings(
            path=self.path,
        )
        self.session._chromium_config["extensions"]["pinned_extensions"].append(self.id)



# TODO implement
# https://www.crx4chrome.com/crx/1148/
# useful to manually export cookies

class EditThisCookie(ChromiumExtension):

    def __init__(self, session):

        raise NotImplementedError



# TODO add a "cookie consent clicker" extension
