__version__ = "0.0.1"

from .client import (
    ClientSession,
)

from .cookiejar import (
    # TODO
    #CookieJar,
    # TODO
    #DummyCookieJar,
    # https://github.com/aio-libs/aiohttp/issues/7998
    # add aiohttp.MozillaCookieJar to load/save cookies.txt files
    MozillaCookieJar,
)
