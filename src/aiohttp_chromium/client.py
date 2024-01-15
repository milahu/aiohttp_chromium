# python stdlib modules
import sys
import os
import re
import urllib.request
import logging
import time
import datetime
import random
import hashlib
import subprocess
import json
import glob
import collections
import zipfile
import base64
import asyncio
import argparse
import atexit
import traceback
import shlex
import shutil
import tempfile
import cgi
import _io
import string
import itertools
import http.cookiejar
import math

from types import (
    SimpleNamespace,
    TracebackType,
)

from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Collection,
    Coroutine,
    Final,
    FrozenSet,
    Generator,
    Generic,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    final,
)



import aiohttp
import aiohttp.client

from aiohttp.client import (
    ClientTimeout,
    DEFAULT_TIMEOUT,
    #_RequestContextManager,
    _BaseRequestContextManager,
    ClientResponse,
)

from aiohttp import (
    hdrs,
    #http,
    #payload,
)

from aiohttp.typedefs import (
    JSONEncoder,
    LooseCookies,
    LooseHeaders,
    StrOrURL,
)

from aiohttp.helpers import (
    # FIXME ImportError: cannot import name '_SENTINEL' from 'aiohttp.helpers'
    #_SENTINEL,
    BasicAuth,
    TimeoutHandle,
    ceil_timeout,
    get_env_proxy_for_url,
    # FIXME ImportError: cannot import name 'method_must_be_empty_body' from 'aiohttp.helpers'
    #method_must_be_empty_body,
    #sentinel,
    strip_auth_from_url,
)

from aiohttp.streams import (
    StreamReader,
)

from aiohttp.base_protocol import (
    BaseProtocol,
)

from aiohttp.client_proto import (
    ResponseHandler,
)

# aiohttp/helpers.py
import enum
_SENTINEL = enum.Enum("_SENTINEL", "sentinel")
sentinel = _SENTINEL.sentinel
import aiohttp.client_reqrep
from aiohttp.client_reqrep import (
    SSL_ALLOWED_TYPES,
    ClientRequest,
    #ClientResponse,
    Fingerprint,
    RequestInfo,
)
if TYPE_CHECKING:
    from ssl import SSLContext
else:
    SSLContext = None

# CIMultiDictProxy is used for resp.headers
from multidict import CIMultiDict, CIMultiDictProxy, MultiDict, MultiDictProxy

from yarl import URL



from . import extensions
#import .extensions
from . import pyrfc6266



# https://github.com/kaliiiiiiiiii/Selenium-Driverless
import selenium_driverless.webdriver as selenium_webdriver
from selenium_driverless.types.by import By # By.ID, By.XPATH, ...
# selenium_webdriver.__package__ == "selenium_driverless"
from selenium_driverless.types.webelement import NoSuchElementException
from selenium_driverless.types.deserialize import StaleJSRemoteObjReference
from cdp_socket.exceptions import CDPError
import cdp_socket



# https://stackoverflow.com/a/77742054/10440128
#from .selenium_mozilla_cookie_jar import SeleniumMozillaCookieJar
#from .cookiejar import MozillaCookieJar



'''
# based on https://stackoverflow.com/a/36077430/10440128
import inspect
async def asyncify(res):
    """
        mix sync and async code.
        f can be sync or async:
        res = await asyncify(f())
    """
    if inspect.isawaitable(res):
        res = await res
    return res
'''



import traceback
def debug_callstack(name):
    stack = "".join(traceback.format_stack())
    logger.debug(f"{name}: called by\n{stack}")



# TODO better?

logging_level = "INFO"
#if options.debug:
if True:
    # TODO disable debug log from selenium (too verbose)
    logging_level = "DEBUG"

logging.basicConfig(
    #format='%(asctime)s %(levelname)s %(message)s',
    # also log the logger %(name)s, so we can filter by logger name
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    level=logging_level,
)

#logger = logging.getLogger("aiohttp_chromium")
logger = logging.getLogger(__name__)

#def logger_print(*args):
#    logger.debug(" ".join(map(str, args)))



# pyppeteer/util.py
import gc
import socket
def get_free_port() -> int:
    """Get free port."""
    sock = socket.socket()
    #sock.bind(('localhost', 0))
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    del sock
    gc.collect()
    return port



# FIXME update aiohttp
# await self._resp.wait_for_close()
class _RequestContextManager(_BaseRequestContextManager[ClientResponse]):
    __slots__ = ()

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
        ) -> None:
        # We're basing behavior on the exception as it can be caused by
        # user code unrelated to the status of the connection.  If you
        # would like to close a connection you must do that
        # explicitly.  Otherwise connection error handling should kick in
        # and close/recycle the connection as required.
        #logger.debug("_RequestContextManager.__aexit__: self._resp.release")
        self._resp.release()
        # FIXME not called
        #logger.debug("_RequestContextManager.__aexit__: self._resp.wait_for_close")
        await self._resp.wait_for_close()



class ClientResponse(aiohttp.client_reqrep.ClientResponse):

    def __init__(
            self,
            method,
            url,
            #writer: "asyncio.Task[None]",
            #continue100: Optional["asyncio.Future[bool]"],
            #timer: Optional[BaseTimerContext],
            #request_info: RequestInfo,
            #traces: List["Trace"],
            loop: asyncio.AbstractEventLoop,
            session,
            _driver_window,
            _request_id,
            _status,
            _status_text,
            _headers,
            _content,
            _filename,
            _filepath,
            _download_is_complete,
        ) -> None:

        #self.session = session
        self._session = session
        self._driver = session._driver
        self._driver_window = _driver_window
        self._request_id = _request_id

        self.status = _status

        self.reason = _status_text

        # TODO http protocol version: 1.0 or 1.1 or 2 or ...
        #self.version = 1234

        self._headers = _headers

        self._content = None

        # suggestedFilename from downloadWillBegin event
        # filename from content-disposition header
        # or basename of url
        self._filename = _filename

        # actual downloaded file
        # basename is response_guid
        self._filepath = _filepath

        # TODO event ...
        self._download_is_complete = _download_is_complete

        self._is_file = _filepath != None

        self._body_str = None
        self._body = None

        if type(_content) == str:
            self._body_str = _content
        elif type(_content) == bytes:
            self._body = _content
        elif _content is None:
            # content is in _filepath
            pass
        else:
            raise ValueError(f"invalid type of content: {type(_content)}")

        self._cache: Dict[str, Any] = {}

        #self._request_info = request_info # TODO

        self._loop = loop



    async def _async_init(self):
        return self
        #raise NotImplementedError



    def __await__(self) -> "ClientResponse":

        """
        async constructor

        session = await aiohttp_chromium.ClientSession()
        # ...
        await session.close()
        """

        #print("ClientResponse.__await__")

        return self._async_init().__await__()



    async def __aenter__(self) -> "ClientResponse":

        """
        async context manager

        async with aiohttp_chromium.ClientSession() as session:
            # ...
        """

        #print("ClientResponse.__aenter__")

        #return self
        return await self



    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> None:
        # similar to _RequestContextManager, we do not need to check
        # for exceptions, response object can close connection
        # if state is broken
        self.release()
        await self.wait_for_close()



    async def text(self, encoding: Optional[str] = None, errors: str = "strict") -> str:
        """Read response payload and decode."""
        if self._body_str:
            return self._body_str
        if self._filepath:
            # dont cache result in self._body
            self._body = b"" # fix: self.get_encoding requires self._body
            logger.debug(f"ClientResponse.text: get_encoding")
            encoding = self.get_encoding() # TODO verify
            self._body = None
            # FIXME handle missing file
            # FIXME handle incomplete file
            while True:
                try:
                    with open(self._filepath, "r", encoding=encoding) as f:
                        return f.read()
                except FileNotFoundError:
                    logger.debug(f"ClientResponse.text: FileNotFoundError {self._filepath}")
                    await asyncio.sleep(1)
        # bytes -> str
        return await super().text(encoding, errors)



    async def read(self) -> bytes:
        """Read response payload."""
        logger.debug(f"ClientResponse.read")
        if self._filepath:
            # dont cache result in self._body
            # FIXME handle missing file
            # FIXME handle incomplete file
            with open(self._filepath, "rb") as f:
                return f.read()
        if self._body is None:
            logger.debug(f"ClientResponse.read: content.read")
            self._body = await self.content.read()
        logger.debug(f"ClientResponse.read: done")
        return self._body

    @property
    def content(self):

        # TODO make this compatible with aiohttp.streams.StreamReader
        # based on io.BytesIO for in-memory data
        # or based on io.BufferedReader for files
        # to provide methods like
        # reader.iter_chunked
        # reader.iter_any

        logger.debug(f"ClientResponse.content")

        if self._content is None:
            if self._filepath:
                # dont use self._body
                # open -> io.BufferedReader
                # FIXME handle missing file
                # FIXME handle incomplete file
                self._content = open(self._filepath, "rb")
            else:
                if self._body is None:
                    logger.debug(f"ClientResponse.content: _body")
                    # str -> bytes
                    self._body = b"" # fix: self.get_encoding requires self._body
                    logger.debug(f"ClientResponse.content: get_encoding")
                    encoding = self.get_encoding()
                    logger.debug(f"ClientResponse.content: _body_str.encode")
                    self._body = self._body_str.encode(encoding)
                logger.debug(f"ClientResponse.content: _content")
                # FIXME use a dummy protocol. no need to pause/resume reading
                #protocol = BaseProtocol() # TODO verify
                logger.debug(f"ClientResponse.content: protocol")
                protocol = ResponseHandler(loop=self._loop) # TODO verify
                logger.debug(f"ClientResponse.content: StreamReader")
                self._content = StreamReader(
                    protocol,
                    limit=len(self._body), # TODO verify
                )
                logger.debug(f"ClientResponse.content: _content.feed_data")
                self._content.feed_data(self._body)
                self._content.feed_eof()
        logger.debug(f"ClientResponse.content: done")
        return self._content

    """
    async def text(self):
        # await response.text()
        if type(self._content) == str:
            return self._content
        return self._content.decode(self.content_encoding)
    """



    async def _wait_complete(self, timeout=60):

        """
        wait until download is complete
        """

        if not self._filepath:
            return True

        return self._download_is_complete

        # FIXME implement timeout

        # TODO better
        # wait for "download completed" event

        raise NotImplementedError



    def release(self):
        # moved to: async def wait_for_close
        #logger.debug(f"ClientResponse.release: noop")
        #debug_callstack("ClientResponse.release")
        return

    async def wait_for_close(self):
        # called by _RequestContextManager.__aexit__
        #logger.debug(f"ClientResponse.wait_for_close: closing driver_window {self._driver_window}")
        #debug_callstack("ClientResponse.wait_for_close")

        # FIXME no. recycle old tabs
        """
        # closing and opening tabs causes chromium to grab window focus
        # close driver_window
        driver = self._driver
        await driver.switch_to.window(self._driver_window)
        await driver.close()
        """
        # instead, mark the window as "old"
        # so it can be re-used or closed by session
        self._session._old_driver_windows.append(self._driver_window)

        if self._content:
            # FIXME AttributeError: 'StreamReader' object has no attribute 'close'
            self._content.close()
        if self._filepath:
            # delete tempfile
            try:
                os.unlink(self._filepath)
            except FileNotFoundError:
                pass
        # TODO? remove event listeners, Network.disable, ...
        # or is this all done by driver.close

    def __del__(self):
        return
        # open(file_path, "rb") -> _io.BufferedReader
        # open(file_path, "r") -> _io.TextIOWrapper
        #if self.content_is_file:
        content_is_file = type(self.content) in {_io.BufferedReader, _io.TextIOWrapper}
        if content_is_file:
            # close file handle and delete file
            # TODO check if self.content is open
            self.content.close()
            # TODO check if self.content_filepath exists
            logger.debug(f"deleting tempfile {self.content_filepath}")
            os.unlink(self.content_filepath)
            # also delete the f"req{request_number}" folder
            os.rmdir(os.path.dirname(self.content_filepath))



class ClientResponseHeaders():
    def __init__(self, headers):
        # headers from the HAR file is list of objects:
        # [ { "name": "x", "value": "y" } ]
        # transform it to a list of tuples, to save memory
        self.headers = []
        if type(headers) == list:
            if len(headers) > 0:
                if type(headers[0]) == dict:
                    if headers[0].get("name") != None and headers[0].get("value") != None:
                        self.headers = list(map(lambda h: (h["name"].lower(), h["value"]), headers))
                    else: raise NotImplementedError(f"parse headers: {repr(headers)}")
                else: raise NotImplementedError(f"parse headers: {repr(headers)}")
        elif type(headers) == dict:
            # note: this can be lossy. header keys can be duplicated
            self.headers = list(map(lambda k: (k.lower(), headers[k]), headers.keys()))
        else: raise NotImplementedError(f"parse headers: {repr(headers)}")
    def get(self, key, default=None):
        # return the first matching header
        # TODO better? how to handle duplicate keys in self.headers
        key = key.lower()
        try:
            return next(h for h in self.headers if h[0] == key)[1]
        except StopIteration: # not found
            #raise KeyError
            return default



default_chromium_extensions = [
    "Ublock", # adblocker
    #"Buster", # captcha solver
    #"EditThisCookie", # manually edit/import/export cookies
]



# aiohttp_chromium.ClientSession

class ClientSession(aiohttp.ClientSession):

    """
    aiohttp interface to chromium

    aka: headful chromium web scraper
    """

    chromium_window_id = None
    vnc_client_list = []
    vnc_client_port = 43022
    connected_vnc_client = None
    xvnc_process = None
    xvnc_port = None
    xvnc_display = None
    xvnc_env = None
    # FIXME dont use picom. just use dark theme + darkreader
    # with picom, captcha images become too ugly (inverted colors)
    #window_manager_name = "icewm"
    window_manager_name = "picom" # needed to invert colors on the xvnc server
    xvnc_invert_colors = True
    is_multi_window = False # "picom" is not a window manager
    window_manager_process = None
    vnc_client_process = None
    ssh_process = None
    ssh_id_file_path = None

    temp_home = None
    downloads_path = None

    chromium_process = None
    chromium_user_data_dir = None
    chromium_config = None
    chromium_config_path = None

    #_selenium_driver = None
    _driver = None
    _old_driver_windows = []

    request_number = 0

    # aiohttp.ClientSession
    closed = True
    cookie_jar = None



    def __init__(
            self,

            # not used. chromium seems to run slower in Xvnc
            # which is detected by cloudflare
            #start_vnc_client=False,
            #vnc_client_list=[],
            #ssh_id_file_path=None,

            cookie_jar = None,

            # if tempdir == None, then this will use tempfile.mkdtemp()
            # if tempdir != None
            # then tempdir is not deleted on cleanup
            tempdir = None,

            # https://docs.aiohttp.org/en/stable/client_quickstart.html#streaming-response-content
            # all downloads are written to disk
            # and deleted on exit of the response context
            # downloading small files to tmpfs gives better performance
            # but if you store the files on disk anyway, tmpfs makes no sense
            # downloading large files to tmpfs can be a problem
            # because tmpfs is limited by the RAM size
            # aiohttp provides a StreamReader in resp.content
            # that behaves like a file handle: resp.content.read(10)
            # by default, use f"{tempdir}/home/Downloads"
            # if tempdir_downloads != None
            # then tempdir_downloads is not deleted on cleanup
            # TODO detect "disk is full" error in chrome://downloads
            tempdir_downloads = None,

            #base_url=None,
            timeout: Union[ClientTimeout, _SENTINEL, None] = sentinel,
            # TODO copy more kwargs from aiohttp.ClientSession.__init__

            _chromium_extensions = default_chromium_extensions,
        ):

        logger.debug(f"ClientSession: init")

        #self._base_url: Optional[URL] = base_url

        loop = asyncio.get_running_loop()
        self._loop = loop

        if timeout is sentinel or timeout is None:
            self._timeout = DEFAULT_TIMEOUT
        else:
            self._timeout = timeout

        self.cookie_jar = cookie_jar

        self._chromium_extensions = _chromium_extensions

        self._keep_env_keys = [
            "PATH",
            # by default, run chromium on the main display
            "DISPLAY",
            # needed to run chromium on the main display
            "XAUTHORITY",
            # use color scheme of the main display
            # light mode or dark mode
            "DBUS_SESSION_BUS_ADDRESS", # /run/user/1000/bus
            "XDG_DATA_DIRS",
            "GTK_THEME",
            "QT_QPA_PLATFORMTHEME",
            "QT_STYLE_OVERRIDE",
            # TODO more?
        ]

        # TODO remove files on cleanup
        self._cleanup_remove_files = []

        if not tempdir:
            tempdir = tempfile.mkdtemp(prefix="aiohttp_chromium.")
            self._cleanup_remove_files.append(tempdir)
        self.tempdir = tempdir

        self.temp_home = f"{self.tempdir}/home"
        os.makedirs(self.temp_home, exist_ok=True)

        user_cache_path = os.environ.get("HOME", "") + "/.cache"

        self._extensions_cache_path = user_cache_path + "/aiohttp_chromium/extensions"
        os.makedirs(self._extensions_cache_path, exist_ok=True)

        self._extensions_path = f"{self.tempdir}/extensions"
        os.makedirs(self._extensions_path, exist_ok=True)

        if not tempdir_downloads:
            tempdir_downloads = f"{self.tempdir}/home/Downloads"
            self._cleanup_remove_files.append(tempdir_downloads)
        self._tempdir_downloads = tempdir_downloads

        # minimal env
        self._environ = {
            "HOME": self.temp_home,
        }
        for key in self._keep_env_keys:
            if key in os.environ:
                self._environ[key] = os.environ[key]

        # force dark mode
        """
        # chromium detects darkmode from gtk theme or from qt theme
        # https://wiki.archlinux.org/title/Dark_mode_switching
        self._environ["GTK_THEME"] = "Breeze-Dark"
        self._environ["XDG_DATA_DIRS"] = f"{self.tempdir}/xdg-data-dirs"
        logger.debug(f"ClientSession: creating XDG_DATA_DIRS: {self.tempdir}/xdg-data-dirs/themes")
        os.makedirs(f"{self.tempdir}/xdg-data-dirs/themes")
        # dont preserve read-only file permissions
        # https://stackoverflow.com/questions/1303413/python-shutil-copytree-ignore-permissions
        # but this will still preserve owner + group?
        _orig_copystat = shutil.copystat
        shutil.copystat = lambda *a, **k: None
        shutil.copytree("/run/current-system/sw/share/themes/Breeze-Dark", f"{self.tempdir}/xdg-data-dirs/themes/Breeze-Dark")
        shutil.copystat = _orig_copystat
        """



    def __await__(self) -> "ClientSession":

        """
        async constructor

        session = await aiohttp_chromium.ClientSession()
        # ...
        await session.close()
        """

        return self._async_init().__await__()



    async def __aenter__(self) -> "ClientSession":

        """
        async context manager

        async with aiohttp_chromium.ClientSession() as session:
            # ...
        """

        #return self
        return await self



    async def _async_init(self):

        # async init function. note: this must "return self"
        # https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init

        logger.debug("ClientSession: starting chromium")
        await self._start_chromium()

        self.closed = False

        driver = self._driver

        """
        # use the first tab for chrome://downloads/
        self._downloads_window = driver.current_window_handle
        await driver.get("chrome://downloads/", timeout=10)
        """

        # this is needed for "def __await__"
        return self



    async def _start_chromium(self):

        self._chromium_user_data_dir = f"{self.tempdir}/chromium-user-data"
        os.makedirs(self._chromium_user_data_dir)

        # FIXME shutil.rmtree fails to delete "chmod 0600" files
        # OSError: [Errno 39] Directory not empty: 'Default'
        #self._cleanup_remove_files.append(self._chromium_user_data_dir + "/Default/Preferences")
        #self._cleanup_remove_files.append(self._chromium_user_data_dir + "/Default")
        # OSError: [Errno 39] Directory not empty: 'chromium-user-data'
        self._cleanup_remove_files.append(self._chromium_user_data_dir + "/Local State")
        # this should be enough
        self._cleanup_remove_files.append(self._chromium_user_data_dir)

        self._chromium_debug_port = get_free_port()

        self._downloads_path = self._tempdir_downloads
        os.makedirs(self._downloads_path, exist_ok=True)

        # TODO expose options
        options = selenium_webdriver.ChromeOptions()
        self._chromium_options = options

        # TODO expose config
        self._chromium_config = {
            "bookmark_bar": {
                # disable bookmarks bar
                "show_on_all_tabs": False,
            },
            "devtools": {
                "preferences": {
                    # devtools: default position is "dock to right"
                    # change position to "dock to bottom"
                    "currentDockState": '"bottom"',
                    # disable async debugger in devtools sources tab
                    "disableAsyncStackTraces": "true",
                    # disable network cache while devtools is open
                    "cacheDisabled": "true",
                },
            },
            "download": {
                # ask where to save each file before downloading
                "prompt_for_download": False,
            },
            "download_bubble": {
                # Show downloads when they're done
                "partial_view_enabled": False,
            },
            "profile": {
                "avatar_index": 26,
                "name": "Person 1",
                "content_settings": {
                    "exceptions": {
                        # allow multiple downloads
                        "automatic_downloads": {
                            #"https://www.opensubtitles.org:443,*": {
                            "*,*": { # TODO test
                                "last_modified": "13345665924169695",
                                "setting": 1
                            },
                        },
                        # allow notifications = allow popups
                        # probably not needed, but avoid the "allow or block" dialog
                        "notifications": {
                            #"https://www.opensubtitles.org:443,*": {
                            "*,*": { # TODO test
                                "last_modified": "13349187584852713",
                                "setting": 1,
                            }
                        },
                        # allow open link in new tab
                        "popups": {
                            #"https://www.opensubtitles.org:443,*": {
                            "*,*": { # TODO test
                                "last_modified": "13348690591551180",
                                "setting": 1,
                            },
                        },
                    },
                },
            },
            "selectfile": {
                # default download location
                "last_directory": self._downloads_path,
            },
            "extensions": {
                "ui": {
                    # needed to load unpacked extensions
                    "developer_mode": True,
                },
                # these 2 are populated by add_*_chromium_extension
                "pinned_extensions": [],
                "settings": {},
                # dark theme
                # FIXME this is not the real dark theme as detected from XDG_DATA_DIRS
                # see also: --enable-features=WebContentsForceDark
                # "theme": {
                #     "id": "autogenerated_theme_id"
                # },
            },
        }

        # force dark mode for web contents
        # similar to darkreader extension, but "less dark"?
        options.add_argument("--enable-features=WebContentsForceDark")

        # disable animations like the download animation
        # https://superuser.com/questions/1738597/how-to-disable-all-chromium-animations
        options.add_argument("--wm-window-animations-disabled")
        options.add_argument("--animation-duration-scale=0")

        for idx, ext in enumerate(self._chromium_extensions):
            if type(ext) == str:
                ext = getattr(extensions, ext)
            ext = await ext(self)
            self._chromium_extensions[idx] = ext

        # write chromium config file
        self._chromium_config_path = self._chromium_user_data_dir + "/Default/Preferences"
        logger.debug(f"writing chromium config file: {self._chromium_config_path}")
        os.makedirs(self._chromium_user_data_dir + "/Default")
        with open(self._chromium_config_path, "w") as f:
            json.dump(self._chromium_config, f, indent=2)

        # TODO expose
        # disable debug messages, these are too verbose
        logging.getLogger("websockets.client").setLevel(logging.WARNING)

        options.add_argument(f"--user-data-dir={self._chromium_user_data_dir}")

        """
        # Don't enforce the same-origin policy
        options.add_argument("--disable-web-security")
        # remove warning: "you are using an unsupported command-line flag"
        options.add_argument("--test-type")
        """

        # default window is too large
        #options.add_argument("--window-size=750,520")
        # (1080 x 720) / 1.5 = 720 x 480
        options.add_argument("--window-size=720,480")

        # based on FlareSolverr/src/undetected_chromedriver/__init__.py
        language = "en-US"
        options.add_argument("--lang=%s" % language)
        #options.add_argument("--headless=new")
        #options.add_argument("--window-size=1920,1080")
        #options.add_argument("--start-maximized") # not working
        #options.add_argument("--no-sandbox") # unsupported

        # Specifies which encryption storage backend to use.
        options.add_argument("--password-store=basic")

        # by default, use chromium from PATH
        # TODO expose option
        self._chromium_executable_path = None
        # no. this fails to load ssl certs
        #self._chromium_executable_path = "/run/current-system/sw/bin/chromium"

        if self._chromium_executable_path:
            options.binary_location = self._chromium_executable_path
            logger.debug(f"_start_chromium: setting options.binary_location = {options.binary_location}")

        chromium_args = dict(
            options=options,
        )

        self._chromium_args = chromium_args

        for ext in self._chromium_extensions:
            await ext.pre_start()

        # run chromium in a clean env
        os_environ = dict(os.environ)
        os.environ.clear()
        os.environ.update(self._environ)
        #logger.debug(f"_start_chromium: self._environ: {json.dumps(self._environ, indent=2)}")

        logger.debug(f"_start_chromium: selenium_webdriver.Chrome")
        driver = await selenium_webdriver.Chrome(**chromium_args)
        self._driver = driver

        # actually start chromium
        logger.debug(f"_start_chromium: driver.start_session")
        await driver.start_session()

        # restore the main env
        os.environ.clear()
        os.environ.update(os_environ)
        del os_environ

        logger.debug(f"_start_chromium: waiting for chromium to start")
        await asyncio.sleep(2)

        # keep this "empty tab" open to keep the window open
        await driver.get("data:text/html,<html><head><title>aiohttp_chromium</title></head><body><pre>this browser is controlled by aiohttp_chromium\n\nplease let it run</pre></body></html>", timeout=10)

        logger.debug(f"_start_chromium: loading cookies")

        # preload cookies before first request
        # https://stackoverflow.com/a/63220249/10440128
        # Network.enable is needed for Network.setCookie
        if self.cookie_jar:
            await driver.execute_cdp_cmd('Network.enable', {})
            for cookie in self.cookie_jar:
                logger.debug("_start_chromium: adding cookie " + repr(cookie))
                # Fix issue Chrome exports 'expiry' key but expects 'expire' on import
                if 'expiry' in cookie:
                    cookie['expires'] = cookie['expiry']
                    del cookie['expiry']
                await driver.execute_cdp_cmd('Network.setCookie', cookie)
            await driver.execute_cdp_cmd('Network.disable', {})

        for ext in self._chromium_extensions:
            await ext.post_start()



    def get(
            self, url: StrOrURL, *, allow_redirects: bool = True, **kwargs: Any
        ) -> "_RequestContextManager":
        """Perform HTTP GET request."""
        # FIXME cleanup of request: close tabs, delete tempfiles
        return _RequestContextManager(
            self._request(hdrs.METH_GET, url, allow_redirects=allow_redirects, **kwargs)
        )



    async def _get_free_driver_window(self):
        # FIXME limit len of self._old_driver_windows
        # if there are too many old windows, close some
        # if we open too many tabs, chromium shows a popup
        # asking to "freeze" unused tabs to reduce memory usage
        try:
            return self._old_driver_windows.pop()
        except IndexError:
            # self._old_driver_windows list is empty
            pass
        # create a new window
        driver_window = await self._driver.switch_to.new_window('tab')
        return driver_window



    async def _request(
            self,
            method: str,
            str_or_url: StrOrURL,
            referrer=None,
            timeout=30,
            allow_redirects=True,
            #**kwargs,
        ) -> ClientResponse:

        assert method == hdrs.METH_GET
        assert allow_redirects == True
        #assert len(kwargs) == 0
        url = str_or_url
        # response urls have no fragment ID
        # also, expected_url can change due to redirects
        expected_url = url.split("#", 1)[0]
        driver = self._driver
        logger.debug(f"_request: url = {repr(url)}")

        driver_window = await self._get_free_driver_window()

        if type(timeout) in {int, float}:   
            timeout = ClientTimeout(total=timeout)

        # based on aiohttp/client.py
        if timeout is sentinel or timeout is None:
            real_timeout: ClientTimeout = self._timeout
        else:
            real_timeout = timeout
        # timeout is cumulative for all request operations
        # (request, redirects, responses, data consuming)
        timeout_handle = TimeoutHandle(
            self._loop,
            real_timeout.total,
            # FIXME AttributeError: 'ClientTimeout' object has no attribute 'ceil_threshold'
            # update aiohttp?
            #ceil_threshold=real_timeout.ceil_threshold
        )
        timeout_handle_handle = timeout_handle.start()

        # FIXME driver.page_source
        # https://github.com/kaliiiiiiiiii/Selenium-Driverless/issues/148
        # driver.page_source fails on non-html pages: CDPError: Could not find node with given id



        target = None

        # pass response_data from responseReceived to downloadWillBegin
        response_data = None

        #response_body = None
        #response_ready = asyncio.Event()
        response_queue = asyncio.Queue()

        # FIXME wait for full page load
        # TODO use custom models of http servers to parse and predict responses
        # TODO wait for networkIdle event (only in puppeteer)
        # TODO waitTillHTMLRendered
        # TODO wait for loading of images -> JS event: DOM...
        # TODO avoid hanging on "infinite load" pages (long poll, gossip, ...)
        # https://github.com/chromedp/chromedp/issues/1044
        # https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-navigate

        expected_request_id = None

        request_url_by_id = dict()

        async def requestWillBeSent(args):
            nonlocal expected_request_id
            request_url = args["request"]["url"]
            # TODO use request_id for logging
            request_id = args["requestId"]
            request_url_by_id[request_id] = request_url
            if request_url != expected_url:
                # this can be REALLY verbose...
                if ignore_url(request_url):
                    return
                #logger.debug(f"requestWillBeSent: ignoring request to {repr(request_url)} != {repr(expected_url)}")
                logger.debug(f"requestWillBeSent {request_id} {request_url}")
                return
            logger.debug(f"requestWillBeSent {request_id} {request_url} setting expected_request_id")
            expected_request_id = request_id
            # TODO? wait until all requests have a response
            # aka "networkIdle"
            #return
            #logger.debug(f"requestWillBeSent {json.dumps(args, indent=2)}")
            #logger.debug(f"requestWillBeSent: " + json.dumps(args, indent=2))
            logger.debug(f"requestWillBeSent {request_id} {request_url}")

        async def requestWillBeSentExtraInfo(args):
            request_id = args["requestId"]
            request_url = request_url_by_id[request_id]
            logger.debug(f"requestWillBeSentExtraInfo {request_id} {request_url} {json.dumps(args, indent=2)}")

        def ignore_url(url):
            if url.startswith("chrome-extension://"):
                return True
            if url.startswith("data:image/png;base64,"):
                return True
            if url.startswith("https://cdn.jsdelivr.net/"):
                return True
            if url.startswith("https://www.recaptcha.net/"):
                return True
            if url.startswith("https://www.gstatic.com/recaptcha/"):
                return True
            if url.startswith("https://www.googletagmanager.com/"):
                return True
            if url.startswith("https://cdn.perfops.net/"):
                return True
            if url.startswith("https://static.opensubtitles.org/"):
                return True
            if url.startswith("https://www.opensubtitles.org/addons/get_user_info.php"):
                return True
            if url.startswith("https://www.opensubtitles.org/cdn-cgi/scripts/"):
                return True
            if url.startswith("https://ads1.opensubtitles.org/"):
                return True
            return False

        async def responseReceived(args):
            nonlocal url
            nonlocal response_data
            #nonlocal response_body
            nonlocal response_queue
            nonlocal response_done
            # TODO better. get target of this response
            nonlocal target
            #logger.debug(f"responseReceived {json.dumps(args, indent=2)}")
            response_url = args["response"]["url"]
            response_status = args["response"]["status"]
            request_id = args["requestId"]
            request_url = request_url_by_id[request_id]

            # FIXME make the url check more loose
            # http == https
            if response_url != expected_url:
                # this can be REALLY verbose...
                if ignore_url(response_url):
                    return
                logger.debug(f"responseReceived: ignoring response {response_status} from {repr(response_url)} != {repr(expected_url)}")
                logger.debug(f"responseReceived {request_id} {request_url} {json.dumps(args, indent=2)}")
                return

            response_done = True

            logger.debug(f"responseReceived: status {response_status}: url {response_url}")
            logger.debug(f"responseReceived {request_id} {request_url} {json.dumps(args, indent=2)}")

            #response_type = args["response"]["headers"]["Content-Type"]

            response_data = args
            #logger.debug(f"response_data: " + json.dumps(response_data, indent=2))
            #logger.debug(f"response headers: " + json.dumps(response_data["response"]["headers"], indent=2))
            if False:
                logger.debug(f"response headers:")
                for key, val in response_data["response"]["headers"].items():
                    logger.debug(f"response header: {key}: {val}")

            def dict_get_ci(_dict, key, default=None):
                """
                get value from dict
                by case-insensitive key

                see also: CIMultiDictProxy
                """
                key = key.lower()
                for _key in _dict.keys():
                    if _key.lower() == key:
                        return _dict[_key]
                return default

            # possible values: inline, attachment, form-data
            #content_disposition = response_data["response"]["headers"].get("content-disposition", "")
            content_disposition = dict_get_ci(response_data["response"]["headers"], "content-disposition", "")

            if content_disposition.startswith("attachment"):

                # response is a file download
                # on file downloads, Network.getResponseBody would hang forever
                logger.debug(f"responseReceived: response is file download -> waiting for downloadWillBegin event")

                # wait for downloadWillBegin event
                # usually (always?) the downloadWillBegin event
                # is fired after the responseReceived event
                return

                # dont read file, it could be too large for RAM
                response_body = None
                # parse filename from content_disposition
                # https://stackoverflow.com/a/73418983/10440128
                """
                value, params = cgi.parse_header(content_disposition)
                if value != "attachment":
                    raise NotImplementedError(f"TODO handle non-attachment content_disposition {repr(content_disposition)}")
                """
                """
                # FIXME can this be empty? can server send attachment without name? why not...
                # TODO then use basename of url as filename
                response_filename = pyrfc6266.parse_filename(content_disposition)
                logger.debug(f"responseReceived: response_filename {response_filename}")
                """

            #else:

            # response is a visible page (html, txt, jpg, ...)
            #logger.debug(f"responseReceived: response is visible page")
            logger.debug(f"responseReceived: Network.getResponseBody sleep")

            # TODO better
            # fix: No data found for resource with given identifier
            await asyncio.sleep(2)

            logger.debug(f"responseReceived: Network.getResponseBody ...")
            args = {
                "requestId": args["requestId"],
            }
            res = await target.execute_cdp_cmd("Network.getResponseBody", args)
            logger.debug(f"responseReceived: Network.getResponseBody done")
            response_body = base64.b64decode(res["body"]) if res["base64Encoded"] else res["body"]
            #logger.debug(f"len(response_body): {len(response_body)}")
            response_filename = None
            #response_filepath = None
            response_guid = None



            # TODO better?
            #response_item = (response_data, response_body, response_filename, response_filepath)
            response_item = (response_data, response_body, response_filename, response_guid)

            logger.debug(f"responseReceived: response_queue.put")
            await response_queue.put(response_item)
            #logger.debug(f"responseReceived {response_status} {response_url} {response_type} " + repr(response_body[:20]) + "...")

        async def responseReceivedExtraInfo(args):
            nonlocal expected_request_id
            nonlocal expected_url
            request_id = args["requestId"]
            # FIXME how dow we know request_url_by_id[request_id]
            # -> requestWillBeSent
            # but url can be missing!
            request_url = request_url_by_id.get(request_id)
            if expected_request_id:
                if request_id != expected_request_id:
                    return
            elif request_url:
                # filter by url
                if request_url != expected_url:
                    return
                expected_request_id = request_id
            logger.debug(f"responseReceivedExtraInfo {request_id} {request_url} {json.dumps(args, indent=2)}")
            #logger.debug(f"responseReceivedExtraInfo {request_id} FIXME parse location header")
            # TODO are these dict keys always lowercase?
            location = args["headers"].get("location")
            if location:
                new_expected_url = str(URL(expected_url).join(URL(location)))
                if expected_url != new_expected_url:
                    logger.debug(f"responseReceivedExtraInfo {request_id} {request_url} changing expected_url from {expected_url} to {new_expected_url}")
                    expected_url = new_expected_url
                    # reverse lookup from url to id
                    # https://stackoverflow.com/a/2569076/10440128
                    # mostly None ...
                    new_expected_request_id = next((id for id, url in request_url_by_id.items() if url == expected_url), None)
                    logger.debug(f"responseReceivedExtraInfo {request_id} {request_url} changing expected_request_id from {expected_request_id} to {new_expected_request_id}")
                    expected_request_id = new_expected_request_id
                else:
                    raise NotImplementedError(f"noop redirect from url {expected_url} to location {location}")

        response_guid = None
        response_done = False

        # FIXME not fired in rare cases
        async def downloadWillBegin(args):
            nonlocal response_data
            nonlocal response_guid
            nonlocal expected_url

            # no. use response_guid
            #response_filepath = self._downloads_path + "/" + response_guid
            #response_done = False
            url = args["url"]
            guid = args["guid"]
            if url != expected_url:
                # ignore this event
                #logger.debug(f"downloadWillBegin: ignoring download from {repr(url)} != {repr(expected_url)}")
                return
                # FIXME why? is expected_url a static variable?
                logger.debug(f"downloadWillBegin {guid} {json.dumps(args, indent=2)}")
                raise Exception(f"downloadWillBegin: unexpected url: {url} != {expected_url}")

            if response_guid:
                if guid != response_guid:
                    # FIXME why? is response_guid a static variable?
                    # are downloads running in parallel?
                    #raise Exception(f"downloadWillBegin: FIXME guid changed from {response_guid} to {guid}")
                    logger.debug(f"downloadWillBegin: guid changed from {response_guid} to {guid}")
                # downloadWillBegin event is fired many many times for the same download
                #return
            response_guid = guid

            #logger.debug(f"downloadWillBegin {guid} {json.dumps(args, indent=2)}")

            response_filename = args["suggestedFilename"]
            if not response_filename:
                logger.debug(f"downloadWillBegin {guid} {json.dumps(args, indent=2)}")
                raise Exception(f"downloadWillBegin: empty response_filename: {repr(response_filename)}")

            logger.debug(f"downloadWillBegin: {guid} -> {response_filename}")

            # wait some time for download to complete

            # FIXME on "downloadProgress: completed", stop waiting in downloadWillBegin
            #for i in range(10):
            for i in range(60):
                await asyncio.sleep(1)
                if response_done:
                    logger.debug(f"downloadWillBegin: download done")
                    break

            if not response_done:
                logger.debug(f"downloadWillBegin: FIXME download is not complete. keep track of downloadProgress events")
                await asyncio.sleep(9999999999999)

            # dont read file, it could be too large for RAM
            response_body = None

            response_item = (response_data, response_body, response_filename, response_guid)

            logger.debug(f"downloadWillBegin: response_queue.put")
            await response_queue.put(response_item)

            # FIXME keep track of downloadProgress events
            # the download has only started but still can fail, or hang forever

        response_received = 0

        async def downloadProgress(args):
            nonlocal response_guid
            nonlocal response_done
            nonlocal response_received
            if response_done:
                # downloadProgress event is fired many many times after state completed
                return
            guid = args["guid"]
            #logger.debug(f"downloadProgress {guid} {json.dumps(args, indent=2)}")
            if guid != response_guid:
                # ignore
                #logger.debug(f"downloadProgress: ignoring download {repr(guid)} != {repr(response_guid)}")
                return
                raise Exception(f"downloadProgress: unexpected guid: {guid} != {response_guid}")
            state = args["state"]
            if state == "completed":
                response_done = True
                logger.debug(f"downloadProgress: completed")
                # FIXME on "downloadProgress: completed", stop waiting in downloadWillBegin
                # put response_item here
                # stop downloadWillBegin from waiting / putting to queue
                #await response_queue.put(response_item)
            elif state == "inProgress":
                received = args["receivedBytes"]
                if received <= response_received:
                    # only show progress if it has changed
                    return
                total = args["totalBytes"]
                if received != total:
                    progress = received / total
                    logger.debug(f"downloadProgress: inProgress {received} / {total} = {progress * 100:.0f}%")
                response_received = received
            # FIXME handle failed downloads
            else:
                logger.debug(f"downloadProgress {guid} {json.dumps(args, indent=2)}")
                raise NotImplementedError(f"downloadProgress: FIXME handle download state {state}")

        async def targetCreated(args):
            # this is called on creation of iframe, frame, tab, ...
            return
            logger.debug(f"targetCreated {json.dumps(args, indent=2)}")

        async def targetInfoChanged(args):
            return
            #logger.debug(f"targetInfoChanged {json.dumps(args, indent=2)}")
            logger.debug("targetInfoChanged")

        async def requestIntercepted(params):
            nonlocal target
            print("requestIntercepted", args)
            url = params["request"]["url"]
            _params = {"interceptionId": params['interceptionId']}
            #if params.get('responseStatusCode') in [301, 302, 303, 307, 308]:
            if False:
                # redirected request
                return await target.execute_cdp_cmd("Network.continueInterceptedRequest", _params)
            fulfill_params = {"headers":params["request"]["headers"]}
            fulfill_params["headers"]["test"] = "Hello World!"
            fulfill_params.update(_params)
            await target.execute_cdp_cmd("Network.continueInterceptedRequest", fulfill_params)
            print(url)

        target = await driver.current_target
        #logger.debug(f"target.id {target.id}")

        # TODO? add cdp listeners only once
        # once per session?
        # once per driver window?

        # enable Target events
        args = {
            "discover": True,
            #"filter": ...
        }
        await target.execute_cdp_cmd("Target.setDiscoverTargets", args)

        await target.add_cdp_listener("Target.targetCreated", targetCreated)
        await target.add_cdp_listener("Target.targetInfoChanged", targetInfoChanged)

        #logger.debug(f"driver.targets {await driver.targets}")

        args = {
            "maxTotalBufferSize": 1_000_000,  # 1GB
            "maxResourceBufferSize": 1_000_000,
            "maxPostDataSize": 1_000_000
        }
        await target.execute_cdp_cmd("Network.enable", args)

        await target.add_cdp_listener("Network.requestWillBeSent", requestWillBeSent)
        await target.add_cdp_listener("Network.responseReceived", responseReceived)

        listen_extra_infos_request = False
        listen_extra_infos_response = True

        if listen_extra_infos_request:
            await target.add_cdp_listener("Network.requestWillBeSentExtraInfo", requestWillBeSentExtraInfo)

        if listen_extra_infos_response:
            await target.add_cdp_listener("Network.responseReceivedExtraInfo", responseReceivedExtraInfo)

        # NOTE these CDP commands must be sent to base_target
        base_target = await driver.base_target
        args = dict(
            behavior = "allowAndName", # use guid as basename
            downloadPath = self._downloads_path,
            eventsEnabled = True, # enable download events
        )
        await base_target.execute_cdp_cmd("Browser.setDownloadBehavior", args)
        await base_target.add_cdp_listener("Browser.downloadWillBegin", downloadWillBegin)
        await base_target.add_cdp_listener("Browser.downloadProgress", downloadProgress)



        if False:

            # intercept requests

            args = {
                "patterns": [{"urlPattern": "*"}],
                #"interceptionStage": "HeadersReceived",
            }
            await target.execute_cdp_cmd("Network.setRequestInterception", args)

            await target.add_cdp_listener("Network.requestIntercepted", requestIntercepted)



        # generic exception handler to cleanup timeout_handle
        try:

            # FIXME timeout is blocking exceptions
            with timeout_handle.timer():

                # retry loop
                # TODO remove?
                while True:

                    try:
                        logger.debug(f"_request: driver.get {repr(url)}")

                        # dont use driver.get(url, timeout=timeout)
                        # because file downloads would always raise TimeoutError
                        # https://github.com/kaliiiiiiiiii/Selenium-Driverless/issues/140

                        await driver.get(
                            url,
                            wait_load=False,
                            referrer=referrer,
                        )

                        # success
                        break

                    except (
                            TimeoutError,
                            asyncio.exceptions.TimeoutError,
                            Exception,
                        ) as e:
                        logger.debug(f"_request: exception {type(e).__name__}: {e} -> retrying")
                        await asyncio.sleep(5)
                        pass



                response_item = None

                # wait for a "good" response
                while True:

                    logger.debug(f"_request: response_queue.get")

                    #logger.debug(f"_request: sleep 999999999"); await asyncio.sleep(999999999)

                    #await response_ready.wait()
                    response_item = await response_queue.get()

                    # TODO better?
                    (response_data, response_body, response_filename, response_guid) = response_item

                    resp_status = response_data["response"]["status"]

                    logger.debug(f"_request: status {resp_status}")

                    #if resp_status in (301, 302, 303, 307, 308) and allow_redirects:
                    # 403 = too many requests -> solve captcha and follow redirect
                    if resp_status in (301, 302, 303, 307, 308, 403) and allow_redirects:
                        title = await self._driver.title
                        logger.debug(f"_request: status {resp_status}: title {title} -> waiting for a better response")
                        # FIXME on actual redirect, change expected_url
                        #await asyncio.sleep(5)
                        continue

                    # found a "good" response
                    break



                # remove event listeners
                # TODO also Network.disable etc?

                await target.remove_cdp_listener("Target.targetCreated", targetCreated)
                await target.remove_cdp_listener("Target.targetInfoChanged", targetInfoChanged)

                await target.remove_cdp_listener("Network.requestWillBeSent", requestWillBeSent)
                await target.remove_cdp_listener("Network.responseReceived", responseReceived)

                if listen_extra_infos_request:
                    await target.remove_cdp_listener("Network.requestWillBeSentExtraInfo", requestWillBeSentExtraInfo)

                if listen_extra_infos_response:
                    await target.remove_cdp_listener("Network.responseReceivedExtraInfo", responseReceivedExtraInfo)

                await base_target.remove_cdp_listener("Browser.downloadWillBegin", downloadWillBegin)
                await base_target.remove_cdp_listener("Browser.downloadProgress", downloadProgress)



                # TODO better?
                (response_data, response_body, response_filename, response_guid) = response_item

                #resp.version = 1 # HTTP-Version
                #resp.status = 200
                #resp.reason = "found"
                #resp.content = 1 # StreamReader
                #resp._headers = 1 # CIMultiDictProxy
                #resp._raw_headers = 1 # RawHeaders

                response_filepath = None
                if response_guid:
                    response_filepath = self._downloads_path + "/" + response_guid

                # FIXME event ...
                # also return incomplete response objects and pass an asyncio event
                # so consumers can wait until the response is completed
                # -> _wait_complete
                # FIXME
                assert response_done == True
                download_is_complete = True

                resp = ClientResponse(
                    method,
                    url,
                    #writer: "asyncio.Task[None]",
                    #continue100: Optional["asyncio.Future[bool]"],
                    #timer: Optional[BaseTimerContext],
                    #request_info: RequestInfo,
                    #traces: List["Trace"],
                    loop=self._loop,
                    session=self,
                    _driver_window=driver_window,
                    _request_id=response_data["requestId"],
                    _status=response_data["response"]["status"],
                    _status_text=response_data["response"]["statusText"],
                    # TODO
                    # examples: "http/1.1", "h2"
                    #_protocol=response_data["response"]["protocol"],
                    # TODO CIMultiDictProxy
                    # NOTE selenium/CDP returns a dict of headers
                    # but the raw headers are a list of key-value pairs
                    # where keys can be repeated
                    _headers=ClientResponseHeaders(response_data["response"]["headers"]),
                    _content=response_body,
                    _filename=response_filename,
                    _filepath=response_filepath,
                    _download_is_complete=download_is_complete,
                )

                return resp

        except BaseException as e:
            # cleanup timeout_handle
            timeout_handle.close()
            if timeout_handle_handle:
                timeout_handle_handle.cancel()
                timeout_handle_handle = None

            raise



    async def close(self) -> None:

        # called by self.__aexit__
        #debug_callstack("ClientSession.close")

        # update cookie_jar
        if self.cookie_jar:
            self.cookie_jar.clear()
            self.cookie_jar.extend(await self._driver.get_cookies())

        # close all windows
        logger.debug(f"ClientSession.close: selenium_driver.quit")
        await self._driver.quit()

        # remove tempfiles
        for temp_path in self._cleanup_remove_files:
            logger.debug(f'ClientSession.close: removing temp path: {temp_path}')
            try:
                # FIXME OSError: [Errno 39] Directory not empty: 'Default'
                # removing temp path: /run/user/1000/asdf/chromium-user-data
                shutil.rmtree(temp_path)
            except NotADirectoryError:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

        self.closed = True

        logger.debug(f"ClientSession.close: done")
