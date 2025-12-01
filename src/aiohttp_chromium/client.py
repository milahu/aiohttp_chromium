# FIXME detect when chromium tabs or windows are closed manually

# FIXME StreamReader._wait_complete is needed
# to wait until a file download is complete
# this must be done via "def downloadProgress"

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
import io
import _io
import string
import itertools
import http.cookiejar
import math
import configparser
import uuid
from collections import OrderedDict

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

import aiohttp.streams

#from aiohttp.streams import StreamReader

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



class _RequestContextManager(_BaseRequestContextManager[ClientResponse]):
    pass



# FIXME refactor to generic class StreamReader
# to handle both files and buffers (on-disk and in-memory)
# https://stackoverflow.com/questions/16752122/dealing-with-trying-to-read-a-file-that-might-not-exist
# bonus points for reading a file that will be created in the future.
# f = open(path) should not wait,
# but await f.read() should wait until the file exists,
# and until the file has some expected size.
# probably based on aiofiles.
# aka "lazy file reader",
# useful to handle file downloads, to wait until the file download is complete
# https://github.com/Tinche/aiofiles
class StreamReaderFile(io.BufferedReader):
    # TODO rename? how does io.BufferedReader work?!
    _filepath = None
    _filehandle = None
    _limit = None
    def __init__(self, _filepath=None, limit=None, **kwargs):
        if kwargs:
            raise NotImplementedError(f"StreamReader.__init__: kwargs = {kwargs}")
        self._filepath = _filepath
        # FIXME what is limit?
        # currently im passing the file size as limit
        # but the file size can be unknown ahead of download ("infinite file", stream)
        self._limit = limit
    def close(self):
        logger.debug(f"StreamReader.close")
        if not self._filehandle:
            # nothing to close
            return
        self._filehandle.close()
        #super().close()
    async def _wait_complete(self, num_bytes=None):
        raise NotImplementedError("StreamReader._wait_complete")
        if num_bytes:
            raise NotImplementedError("StreamReader._wait_complete: num_bytes != None")
        if not self._limit:
            raise NotImplementedError("StreamReader._wait_complete: self._limit == None")
        while True:
            try:
                # TODO self._limit or self._filesize
                if os.path.getsize(self._filepath) == self._limit:
                    return
            except FileNotFoundError:
                pass
            #except Exception as e:
            #    logger.debug(f"StreamReader._wait_complete: e {type(e)} {e}")
            sleep_step = 1 # TODO expose
            await asyncio.sleep(sleep_step)
    async def _open_file(self):
        """
        wait until the file exists, then open the file
        """
        logger.debug(f"StreamReader._open_file")
        if self._filehandle:
            return
        while True:
            try:
                # TODO use aiofiles
                self._filehandle = open(self._filepath, "rb")
                return
            except FileNotFoundError:
                pass
            sleep_step = 1 # TODO expose
            logger.debug(f"StreamReader._open_file: waiting until file exists")
            await asyncio.sleep(sleep_step)
    async def read(self, num_bytes=None):
        logger.debug(f"StreamReader.read")
        if self._filepath:
            if not self._filehandle:
                # NOTE this will wait until the file is created
                # so this can wait forever if the file is never created
                await self._open_file()
            # TODO use aiofiles
            #return await self._filehandle.read()
            if num_bytes:
                await self._wait_complete(num_bytes)
                # TODO verify
                return self._filehandle.read(num_bytes)
            await self._wait_complete()
            return self._filehandle.read()
        #if not self._filepath:
        raise NotImplementedError("self._filepath == None")



class ClientResponse(aiohttp.client_reqrep.ClientResponse):

    _content = None

    # TODO set self._filesize from expected size of download
    # TODO what if actual download size is different?
    _filesize = None

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

        self.method = method

        self.status = _status

        self.reason = _status_text

        # TODO http protocol version: 1.0 or 1.1 or 2 or ...
        #self.version = 1234

        self._headers = _headers

        # suggestedFilename from downloadWillBegin event
        # filename from content-disposition header
        # or basename of url
        self._filename = _filename

        # actual downloaded file
        # basename is response_guid
        self._filepath = _filepath

        # TODO event ...
        self._download_is_complete = _download_is_complete

        # FIXME the filesize can be unknown ahead of time
        # FIXME responseReceived: response is file download -> waiting for downloadWillBegin event
        content_length = self._headers.get("content-length", None)
        if content_length:
            self._filesize = int(content_length)

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

                self._StreamReader = StreamReaderFile

                self._content = self._StreamReader(
                    _filepath=self._filepath,
                    limit=self._filesize,
                )

                """
                # dont use self._body
                # open -> io.BufferedReader
                # FIXME handle missing file
                # FIXME handle incomplete file
                # FIXME remove open
                # FIXME FileNotFoundError: download file can be missing
                # response.content should be lazy:
                # it should also work on incomplete responses
                # and only (await response.content.read()) should wait until the response is complete
                if not os.path.exists(self._filepath):
                    d = os.path.dirname(self._filepath)
                    logger.debug(f"ClientResponse.content: FIXME missing file {repr(self._filepath)}. files in {repr(d)}: {os.listdir(d)}")
                # NOTE self._filepath can be an incomplete download
                # TODO when download is complete, signal from cdp event listenr to response
                self._content = open(self._filepath, "rb")
                """

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
                self._StreamReader = aiohttp.streams.StreamReader
                self._content = self._StreamReader(
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
            return

        # FIXME filesize can be unknown: self._filesize == None
        assert self._filesize != None

        t1 = time.time()

        while True:
            try:
                if os.path.getsize(self._filepath) == self._filesize:
                    return
            except FileNotFoundError:
                pass

            #except Exception as e:
            #    logger.debug(f"ClientResponse._wait_complete: e {type(e)} {e}")

            if timeout != None:
                t2 = time.time()
                dt = t2 - t1
                if dt > timeout:
                    raise TimeoutError

            sleep_step = 1 # TODO expose
            await asyncio.sleep(sleep_step)

        # TODO better
        # wait for "download completed" event

        raise NotImplementedError



    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
        ) -> None:
        print(f"ClientResponse.__aexit__ 665")
        # called by _RequestContextManager.__aexit__
        #logger.debug(f"ClientResponse.__aexit__: closing driver_window {self._driver_window}")
        #debug_callstack("ClientResponse.__aexit__")

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
            # FIXME remove open
            if isinstance(self._content, io.BufferedReader):
                # open(file_path, "rb")
                self._content.close()
            #elif isinstance(self._content, io.TextIOWrapper):
            #    # open(file_path, "r")
            #    self._content.close()
            # FIXME refactor to generic class StreamReader
            elif isinstance(self._content, aiohttp.streams.StreamReader):
                del self._content
            elif type(self._content).__name__ == "StreamReader":
                del self._content
            elif type(self._content).__name__ == "StreamReaderFile":
                del self._content
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
    "DarkReader", # nightmode
    #"Buster", # captcha solver
    #"EditThisCookie", # manually edit/import/export cookies
    "NoDownloadShelf", # remove downloads shelf
    "ClearDownloads", # remove finished downloads
]



# aiohttp_chromium.ClientSession

class ClientSession(aiohttp.ClientSession):

    """
    aiohttp interface to chromium

    aka: headful chromium web scraper
    """

    _debug2 = False

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

            # with (_prevent_focus_stealing = True)
            # use this regex to create one rule to match all instances
            # when tempdir is set (tempdir != None)
            # and this is unset (_tempdir_regex == None)
            # then _prevent_focus_stealing will create a new rule for every new instance
            # _tempdir_regex = None,

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

            _headless = False,

            _chromium_options = {},

            # in headful mode (_headless = False)
            # prevent the chromium window from stealing focus
            _prevent_focus_stealing = True,
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

        self._user_chromium_options = _chromium_options

        self._headless = _headless

        self._prevent_focus_stealing = _prevent_focus_stealing

        self._keep_env_keys = [
            "PATH",
            # by default, run chromium on the main display
            "DISPLAY",
            # needed to run chromium on the main display
            "XAUTHORITY",
            # use color scheme of the main display
            # light mode or dark mode
            # NOTE dbus can fail: org.freedesktop.DBus.Error.UnknownMethod: No such interface “org.freedesktop.portal.Settings” on object at path /org/freedesktop/portal/desktop
            # quickfix: set GTK_THEME=Breeze-Dark
            "DBUS_SESSION_BUS_ADDRESS", # /run/user/1000/bus
            "XDG_DATA_DIRS", # /themes/Breeze-Dark
            "GTK_THEME",
            "QT_QPA_PLATFORMTHEME",
            "QT_STYLE_OVERRIDE",
            # TODO more?
        ]

        # TODO remove files on cleanup
        self._cleanup_remove_files = []

        # self._tempdir_regex = _tempdir_regex

        if not tempdir:
            tempdir_prefix = "aiohttp_chromium."
            # this assumes that tempfile.mkdtemp appends 8 random chars after the prefix
            tempdir_random_len = 8
            tempdir = tempfile.mkdtemp(prefix=tempdir_prefix)
            self._cleanup_remove_files.append(tempdir)
            actual_tempdir_prefix = tempdir[-tempdir_random_len-len(tempdir_prefix):-tempdir_random_len]
            assert actual_tempdir_prefix == tempdir_prefix, f"bad tempdir format of tempdir {tempdir!r}"
            # overwrite self._tempdir_regex
            # self._tempdir_regex = re.escape(tempdir[:-tempdir_random_len]) + "[0-9a-zA-Z_]{" + str(tempdir_random_len) + "}"
        self.tempdir = tempdir
        logger.debug(f"ClientSession: using tempdir {self.tempdir}")

        r"""
        if not self._tempdir_regex:
            # _tempdir_regex will work only for this instance
            self._tempdir_regex = re.escape(self.tempdir)
        """

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
        # workaround for "dbus can fail"
        # TODO install Breeze-Dark theme to cache, to make this portable
        # TODO expose option for darkmode
        self._environ["GTK_THEME"] = "Breeze-Dark"

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

        self._chromium_user_data_dir = f"{self.tempdir}/aiohttp-chromium-user-data"
        if self._prevent_focus_stealing:
            self._chromium_user_data_dir += "-with-pfs"
        os.makedirs(self._chromium_user_data_dir)

        # do this before creating the chromium window
        if not self._headless and self._prevent_focus_stealing:
            self._enable_prevent_focus_stealing()

        logger.debug(f"ClientSession: using chromium user-data-dir {self._chromium_user_data_dir}")

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
        self._chromium_state = {
            "browser": {
                "enabled_labs_experiments": [
                    # remove the "Enable featured Experiments" button
                    "chrome-labs@3",
                    # remove the "Show side panel" button
                    "hide-sidepanel-button",
                    # remove the profile button
                    "show-avatar-button@3",
                    # remove downloads bubble
                    # instead, chromium will show the downloads shelf
                    # downloads shelf is removed by NoDownloadShelf extension
                    "download-bubble@2",
                    # remove the "close tab" buttons
                    # to prevent accidental closing of tabs
                    "hide-tab-close-buttons",
                    # remove the "tab search" button. not needed
                    "remove-tabsearch-button",
                    # dont switch tabs on scroll
                    # to prevent accidental switching of tabs
                    "scroll-tabs@2",
                    # disable: Close window with last tab
                    "close-window-with-last-tab@1",
                ]
            }
        }

        # TODO expose config
        self._chromium_config = {
            "browser": {
                # use system title bar and borders
                "custom_chrome_frame": False,
            },
            "in_product_help": {
                "snoozed_feature": {
                    "IPH_HighEfficiencyMode": {
                        # disable "memory saver"
                        # instead, limit number of open tabs
                        "is_dismissed": True,
                    },
                },
            },
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
                "default_content_setting_values": {
                    # disable notifications by default
                    #"notifications": 2,
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

        # dont auto-reload pages on network errors
        # otherwise, switching tabs would reload failed requests
        options.add_argument("--disable-auto-reload")

        for idx, ext in enumerate(self._chromium_extensions):
            if type(ext) == str:
                ext = getattr(extensions, ext)
            ext = await ext(self)
            self._chromium_extensions[idx] = ext

        # write chromium config file
        self._chromium_config_path = self._chromium_user_data_dir + "/Default/Preferences"
        logger.debug(f"writing chromium config file: {self._chromium_config_path}")
        os.makedirs(self._chromium_user_data_dir + "/Default", exist_ok=True)
        with open(self._chromium_config_path, "w") as f:
            json.dump(self._chromium_config, f, indent=2)

        # write chromium state file
        self._chromium_state_path = self._chromium_user_data_dir + "/Local State"
        logger.debug(f"writing chromium state file: {self._chromium_state_path}")
        with open(self._chromium_state_path, "w") as f:
            json.dump(self._chromium_state, f)

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
        w, h = self._user_chromium_options.get("window_size", (720, 480))
        options.add_argument(f"--window-size={w},{h}")

        # based on FlareSolverr/src/undetected_chromedriver/__init__.py
        language = "en-US"
        options.add_argument("--lang=%s" % language)

        if self._headless:
            options.add_argument("--headless=new")

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



    def _enable_prevent_focus_stealing(self):
        # TODO use a more strict check to detect KDE window manager
        is_kde_wm = shutil.which("qdbus") != None
        if is_kde_wm:
            return self._enable_prevent_focus_stealing_kde()
        # TODO add more window managers
        logger.debug(f"_enable_prevent_focus_stealing_kde: reading config file {kwinrulesrc_path!r}")



    def _enable_prevent_focus_stealing_kde(self):
        # https://docs.kde.org/stable5/en/kwin/kcontrol/windowbehaviour/#focus-focusstealing
        # https://github.com/sandorex/kcfg
        # https://discuss.kde.org/t/can-kwin-reload-window-rules-kwinrulesrc-dynamically-via-cli-without-full-reconfigure/34136
        # no, this creates too many rules
        # chromium_user_data_dir_regex = self._tempdir_regex + re.escape("/aiohttp-chromium-user-data")
        chromium_user_data_dir_regex = r".*/aiohttp-chromium-user-data-with-pfs"
        kwinrulesrc_path = "~/.config/kwinrulesrc"
        kwinrulesrc_path = os.path.expanduser(kwinrulesrc_path) # expand "~"
        config = configparser.ConfigParser()
        config.optionxform = str # preserves the case
        if os.path.exists(kwinrulesrc_path):
            logger.debug(f"_enable_prevent_focus_stealing_kde: reading config file {kwinrulesrc_path!r}")
            with open(kwinrulesrc_path) as fp:
                config.read_string(fp.read())
            logger.debug(f"_enable_prevent_focus_stealing_kde: reading config file done -> sections {config.sections()}")
            # decode backslash-escapes: "\\\\" -> "\\"
            # https://stackoverflow.com/a/69772725/10440128
            for section in config.sections():
                for key, val in config[section].items():
                    config[section][key] = val.encode('raw_unicode_escape').decode('unicode_escape')
            config_dict = {section: dict(config[section]) for section in config.sections()}
            logger.debug(f"_enable_prevent_focus_stealing_kde: reading config file done -> config_str {json.dumps(config_dict, indent=2)}")
        # TODO also handle forks of chromium
        wmclass_regex = "chromium-browser \\(" + chromium_user_data_dir_regex + "\\) Chromium-browser"
        rule = {
            "Description": "aiohttp_chromium: prevent focus stealing",
            "clientmachine": "localhost",
            "title": "", # actual window title. this is dynamic
            "fsplevel": "4", # "extreme"
            "fsplevelrule": "2",
            "types": "1",
            "windowrole": "browser",
            "windowrolematch": "1",
            "wmclass": wmclass_regex,
            "wmclasscomplete": "true",
            "wmclassmatch": "3", # regex
        }
        # check if rule exists
        for rule_id in config.sections():
            if rule_id == "General": continue
            existing_rule = config[rule_id]
            found_rule = False
            for key, val in rule.items():
                existing_val = existing_rule.get(key)
                if existing_val == val:
                    found_rule = True
                else:
                    # logger.debug(f"_enable_prevent_focus_stealing_kde: rules mismatch on key {key}: {val!r} != {existing_val!r}")
                    found_rule = False
                    break
            if found_rule:
                logger.debug(f"_enable_prevent_focus_stealing_kde: found existing rule {json.dumps(dict(existing_rule), indent=2)}")
                return
        # TODO dont add General section?
        # the General section can be removed by KDE...
        if not "General" in config:
            # init config (or fix broken config)
            rule_count = len(config.sections())
            rule_ids = ",".join(config.sections())
            section_key = "General"
            config.add_section(section_key)
            # TODO? use config.set("General", "count", "0")
            section = config._sections.pop(section_key)
            section["count"] = str(rule_count)
            section["rules"] = rule_ids
            logger.debug(f"_enable_prevent_focus_stealing_kde: adding General section {json.dumps(dict(section), indent=2)}")
            # move section to top
            config._sections = OrderedDict(
                [(section_key, section)] + list(config._sections.items())
            )
            logger.debug(f"_enable_prevent_focus_stealing_kde: adding General section done -> sections {config.sections()}")

        # add rule
        logger.debug(f"_enable_prevent_focus_stealing_kde: adding rule {json.dumps(dict(rule), indent=2)}")
        config["General"]["count"] = str(int(config["General"].get("count", 0)) + 1)
        rule_uuid = str(uuid.uuid4())
        config["General"]["rules"] = ",".join(config["General"].get("rules", "").split(",") + [rule_uuid])
        # rule = {key: str(val) for key, val in rule.items()} # option values must be strings
        config[rule_uuid] = rule
        logger.debug(f"_enable_prevent_focus_stealing_kde: adding rule done -> sections {config.sections()}")
        # config_dict = {section: dict(config[section]) for section in config.sections()}
        # logger.debug(f"_enable_prevent_focus_stealing_kde: adding rule done -> config {json.dumps(config_dict, indent=2)}")
        # encode backslash-escapes: "\\" -> "\\\\"
        # https://stackoverflow.com/a/69772725/10440128
        # fix: escaped regex parens in rule["wmclass"] are lost: "\\(" and "\\)" are written as "\\"
        for section in config.sections():
            for key, val in config[section].items():
                config[section][key] = val.encode('unicode_escape').decode('raw_unicode_escape')
        logger.debug(f"_enable_prevent_focus_stealing_kde: writing config file {kwinrulesrc_path!r}")
        os.makedirs(os.path.dirname(kwinrulesrc_path), exist_ok=True)
        with open(kwinrulesrc_path, "w") as fp:
            config.write(fp, space_around_delimiters=False)
        with open(kwinrulesrc_path) as fp:
            config_str = fp.read()
        logger.debug(f"_enable_prevent_focus_stealing_kde: writing config file done -> config_str:\n{config_str}")
        # reload rules
        args = "qdbus org.kde.KWin /KWin reconfigure".split()
        logger.debug(f"_enable_prevent_focus_stealing_kde: reloading rules: {shlex.join(args)}")
        subprocess.run(args)
        with open(kwinrulesrc_path) as fp:
            config_str = fp.read()
        logger.debug(f"_enable_prevent_focus_stealing_kde: reloading rules done -> config_str:\n{config_str}")



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

            # FIXME handle kwargs
            headers=None,
            trace_request_ctx=None,

            _cdp_listeners=None,
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

        # FIXME handle kwargs
        logger.debug(f"_request: headers = {headers!r}")
        logger.debug(f"_request: trace_request_ctx = {trace_request_ctx!r}")

        driver_window = await self._get_free_driver_window()

        # note: we have to pass activate=True
        # https://github.com/kaliiiiiiiiii/Selenium-Driverless/issues/342
        await self._driver.switch_to.window(driver_window, activate=True)

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
        download_data = None

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
            if expected_request_id:
                # filter by request_id
                if request_id != expected_request_id:
                    return
            else:
                # expected_request_id is unknown
                # filter by request_url
                if request_url != expected_url:
                    # this can be REALLY verbose...
                    if ignore_url(request_url):
                        return
                    #logger.debug(f"requestWillBeSent: ignoring request to {repr(request_url)} != {repr(expected_url)}")
                    logger.debug(f"requestWillBeSent {request_id} {request_url}")
                    return
                logger.debug(f"requestWillBeSent {request_id} {request_url} setting expected_request_id")
                # set this only here
                # request_id stays constant over redirects
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
            if url.startswith("https://z-na.amazon-adsystem.com/"):
                return True

            if url.startswith("https://static.opensubtitles.org/"):
                return True
            if url.startswith("https://www.opensubtitles.org/addons/get_user_info.php"):
                return True
            if url.startswith("https://www.opensubtitles.org/cdn-cgi/scripts/"):
                return True
            if url.startswith("https://ads1.opensubtitles.org/"):
                return True
            if url.startswith("https://toplist.cz/"):
                return True

            return False

        async def responseReceived(args):
            nonlocal url
            nonlocal response_data
            nonlocal download_data
            #nonlocal response_body
            nonlocal response_queue
            nonlocal response_done
            # TODO better. get target of this response
            nonlocal target

            if args == None:
                # this should never happen
                raise Exception(f"responseReceived: args == None")

            #logger.debug(f"responseReceived {json.dumps(args, indent=2)}")
            response_url = args["response"]["url"]
            response_status = args["response"]["status"]
            request_id = args["requestId"]
            if request_id != expected_request_id:
                if self._debug2:
                    logger.debug(f"responseReceived {request_id} ignoring response {response_status}")
                return
            try:
                request_url = request_url_by_id[request_id]
            except KeyError:
                # this can happen during cleanup
                # TODO verify
                logger.debug(f"responseReceived {request_id} ignoring response with unknown url")
                return

            # FIXME make the url check more loose
            # http == https
            """
            if response_url != expected_url:
                # this can be REALLY verbose...
                if ignore_url(response_url):
                    return
                logger.debug(f"responseReceived {request_id} ignoring response {response_status} from {repr(response_url)} != {repr(expected_url)}")
                #logger.debug(f"responseReceived {request_id} {request_url} {json.dumps(args, indent=2)}")
                return
            """

            response_done = True

            logger.debug(f"responseReceived {request_id} status {response_status}: url {response_url}")
            #logger.debug(f"responseReceived {request_id} {request_url} {json.dumps(args, indent=2)}")

            #response_type = args["response"]["headers"]["Content-Type"]

            response_data = args
            #logger.debug(f"responseReceived {request_id} response_data: " + json.dumps(response_data, indent=2))
            #logger.debug(f"responseReceived {request_id} response headers: " + json.dumps(response_data["response"]["headers"], indent=2))

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

                # response is attachment (file download)
                # on file downloads, Network.getResponseBody would hang forever

                response_data = args

                if download_data:
                    # download_data was set by downloadWillBegin
                    await finish_download_response(response_data, download_data)
                else:
                    logger.debug(f"responseReceived {request_id} response is file download -> waiting for downloadWillBegin event")

                # dont read file, it could be too large for RAM
                #response_body = None
                return

            #else:
            # response is inline content (html, txt, jpg, ...)
            #logger.debug(f"responseReceived {request_id} response is visible page")
            logger.debug(f"responseReceived {request_id} Network.getResponseBody sleep")

            # TODO better
            # fix: No data found for resource with given identifier
            await asyncio.sleep(2)

            # FIXME this can hang, producing a TimeoutError
            # better use Network.takeResponseBodyForInterceptionAsStream
            # instead of Network.getResponseBody

            logger.debug(f"responseReceived {request_id} Network.getResponseBody ...")
            args = {
                "requestId": args["requestId"],
            }
            res = await target.execute_cdp_cmd("Network.getResponseBody", args)
            logger.debug(f"responseReceived {request_id} Network.getResponseBody done")
            response_body = base64.b64decode(res["body"]) if res["base64Encoded"] else res["body"]
            #logger.debug(f"len(response_body): {len(response_body)}")
            response_filename = None
            #response_filepath = None
            response_guid = None



            # TODO better?
            #response_item = (response_data, response_body, response_filename, response_filepath)
            response_item = (response_data, response_body, response_filename, response_guid)

            logger.debug(f"responseReceived {request_id} response_queue.put")
            await response_queue.put(response_item)
            #logger.debug(f"responseReceived {response_status} {response_url} {response_type} " + repr(response_body[:20]) + "...")

        async def responseReceivedExtraInfo(args):
            # FIXME the responseReceivedExtraInfo can be missing
            # so dont use this to modify expected_url
            nonlocal expected_request_id
            nonlocal expected_url
            request_id = args["requestId"]
            # FIXME how dow we know request_url_by_id[request_id]
            # -> requestWillBeSent
            # but url can be missing!
            request_url = request_url_by_id.get(request_id)
            if request_id != expected_request_id:
                return
            #logger.debug(f"responseReceivedExtraInfo {request_id} {request_url} {json.dumps(args, indent=2)}")
            logger.debug(f"responseReceivedExtraInfo {request_id} {request_url}")
            # TODO are these dict keys always lowercase?
            location = args["headers"].get("location")
            if location:
                # TODO populate response.history = list of intermediary responses
                new_expected_url = str(URL(expected_url).join(URL(location)))

                # quickfix: upgrade redirect to https
                # see also doc/redirect-http-https.txt
                if new_expected_url.startswith("http:"):
                    logger.debug(f"responseReceivedExtraInfo {request_id} {request_url} upgrading redirect to https")
                    new_expected_url = "https:" + new_expected_url[5:]

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

            # response_data was set by responseReceived
            # in most cases, responseReceived is called before downloadWillBegin
            nonlocal response_data
            nonlocal download_data

            # guid = download id
            nonlocal response_guid

            nonlocal expected_url

            if args == None:
                # this should never happen
                raise Exception(f"downloadWillBegin: args == None")

            # no. use response_guid
            #response_filepath = self._downloads_path + "/" + response_guid
            #response_done = False
            url = args["url"]
            guid = args["guid"]
            # FIXME filter by request_id?
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

            download_data = args

            if response_data:
                # response_data was set by responseReceived
                await finish_download_response(response_data, download_data)
            else:
                logger.debug(f"downloadWillBegin: response_data is missing -> waiting for responseReceived event")

        # called from downloadWillBegin or responseReceived
        # in most cases, responseReceived comes before downloadWillBegin
        # but downloadWillBegin can come before responseReceived

        async def finish_download_response(response_data, download_data):

            url = download_data["url"]
            guid = download_data["guid"]

            response_guid = guid

            logger.debug(f"finish_download_response {guid} {json.dumps(download_data, indent=2)}")

            response_filename = download_data["suggestedFilename"]
            if not response_filename:
                logger.debug(f"finish_download_response {guid} {json.dumps(download_data, indent=2)}")
                raise Exception(f"finish_download_response: empty response_filename: {repr(response_filename)}")

            logger.debug(f"finish_download_response: {guid} -> {response_filename}")

            # wait some time for download to complete

            # FIXME on "downloadProgress: completed", stop waiting in downloadWillBegin
            #for i in range(10):
            for i in range(60):
                await asyncio.sleep(1)
                if response_done:
                    logger.debug(f"finish_download_response: download done")
                    break

            if not response_done:
                logger.debug(f"finish_download_response: FIXME download is not complete. keep track of downloadProgress events")
                await asyncio.sleep(9999999999999)

            # dont read file, it could be too large for RAM
            response_body = None

            response_item = (response_data, response_body, response_filename, response_guid)

            logger.debug(f"finish_download_response: response_queue.put")
            await response_queue.put(response_item)

            # FIXME keep track of downloadProgress events
            # the download has only started but still can fail, or hang forever

        response_received = 0

        async def downloadProgress(args):
            # TODO detect when download hangs for too long
            # when receivedBytes stays constant below totalBytes
            nonlocal response_guid
            nonlocal response_done
            nonlocal response_received
            guid = args["guid"]
            if self._debug2:
                logger.debug(f"downloadProgress {guid} {json.dumps(args, indent=2)}")
            if response_done:
                # downloadProgress event is fired many many times after state completed
                return
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

        # lifecycle of request
        # requestWillBeSent: set expected_request_id
        # responseReceived
        # responseReceivedExtraInfo
        # requestWillBeSent: if redirect, has the same request_id
        # responseReceived
        # responseReceivedExtraInfo
        # downloadWillBegin
        # downloadProgress
        # downloadProgress
        # downloadProgress
        # ...
        # NOTE downloadWillBegin can come before responseReceived

        # increase maximum buffer size to 1.2GB
        # fix: Request content was evicted from inspector cache
        max_buffer_size = 1_200_000_000
        args = {
            "maxTotalBufferSize": max_buffer_size,
            "maxResourceBufferSize": max_buffer_size,
            "maxPostDataSize": max_buffer_size,
        }
        await target.execute_cdp_cmd("Network.enable", args)

        await target.add_cdp_listener("Network.requestWillBeSent", requestWillBeSent)
        await target.add_cdp_listener("Network.responseReceived", responseReceived)

        if _cdp_listeners is None:
            _cdp_listeners = dict()

        for key, val in _cdp_listeners.items():
            if key == "responseReceived":
                key = "Network.responseReceived"
            elif key == "requestWillBeSent":
                key = "Network.requestWillBeSent"
            #await target.add_cdp_listener(key, val)
            # wrap the listener
            # TODO test this with multiple listeners
            # is the relay_cdp_event function overwritten?
            # do we have to copy the function?
            async def relay_cdp_event(args):
                return await val(args, driver, target)
            await target.add_cdp_listener(key, relay_cdp_event)
        # TODO cleanup? are listeners cleaned up automatically?

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

            # NOTE timeout applies only to request, not to response
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

        except BaseException as e:
            # cleanup timeout_handle
            timeout_handle.close()
            if timeout_handle_handle:
                timeout_handle_handle.cancel()
                timeout_handle_handle = None

            # mark the window as "old"
            # so it can be re-used or closed by session
            self._old_driver_windows.append(driver_window)

            raise

        # removed: try
        if True:

            # removed: with
            if True:

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

                    # TODO test: allow_redirects == False

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



    async def close(self) -> None:

        # called by self.__aexit__
        #debug_callstack("ClientSession.close")

        # update cookie_jar
        if self.cookie_jar:
            self.cookie_jar.clear()
            self.cookie_jar.extend(await self._driver.get_cookies())

        for ext in self._chromium_extensions:
            await ext.close()

        # close all windows
        logger.debug(f"ClientSession.close: selenium_driver.quit")
        await self._driver.quit()

        # remove tempfiles
        for temp_path in self._cleanup_remove_files:
            logger.debug(f'ClientSession.close: removing temp path: {temp_path}')
            try:
                # FIXME OSError: [Errno 39] Directory not empty: 'Default'
                # removing temp path: /run/user/1000/asdf/aiohttp-chromium-user-data
                shutil.rmtree(temp_path)
            except NotADirectoryError:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

        self.closed = True

        logger.debug(f"ClientSession.close: done")
