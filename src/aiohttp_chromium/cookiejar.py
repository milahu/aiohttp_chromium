import http.cookiejar
from pathlib import Path
from typing import Union


PathLike = Union[str, "os.PathLike[str]"]


class MozillaCookieJar(list):

    """
    load/save cookies from/to a cookies.txt file with selenium

    convert between http.cookiejar.MozillaCookieJar and list of cookie_dict

    ```
    from SeleniumMozillaCookieJar import SeleniumMozillaCookieJar
    from selenium import webdriver

    driver = webdriver.Chrome()
    driver.get("http://www.google.com")

    cookiejar = SeleniumMozillaCookieJar()

    # copy cookies from driver to cookiejar
    # cookiejar is a list of dicts
    cookiejar.extend(driver.get_cookies())

    # save cookies
    cookiejar.save("cookies.txt")

    # load cookies
    cookiejar.load("cookies.txt")

    # copy cookies from cookiejar to driver
    for cookie in cookiejar:
        driver.add_cookie(cookie)

    driver.quit()
    ```

    cookies.txt format
    domain domain_initial_dot path secure expires name value

    see also
    https://stackoverflow.com/questions/61652777
    """


    def load(self, file_path: PathLike):

        file_path = Path(file_path)

        jar_1 = http.cookiejar.MozillaCookieJar()
        jar_1.load(file_path)

        self.clear() # delete old cookies

        for cookie_1 in jar_1:
            #print("cookie_1 dir", dir(cookie_1))
            #import json
            #print("cookie_1 dict", json.dumps(cookie_1.__dict__, indent=2))
            cookie = {
                # required values
                "name": cookie_1.name,
                "value": cookie_1.value,
                # optional values
                "domain": cookie_1.domain,
                "path": cookie_1.path,
                "expires": cookie_1.expires, # UTC timestamp
                "httpOnly": True, # TODO?
                "secure": cookie_1.secure,
                "session": False, # TODO?
                "sameSite": "Lax" if cookie_1.domain_initial_dot else "Strict", # TODO?
            }
            self.append(cookie)
            #driver.add_cookie(cookie)
            #await driver.add_cookie(cookie)

        del jar_1


    def save(self, file_path: PathLike) -> None:

        file_path = Path(file_path)

        # save cookies
        jar_1 = http.cookiejar.MozillaCookieJar()

        for cookie in self:
            name = cookie["name"]
            domain = cookie["domain"]
            path = cookie["path"]
            cookie_1 = http.cookiejar.Cookie(
                0, # version
                name, # name
                cookie["value"], # value
                None, # port
                False, # port_specified
                domain, # domain
                False, # domain_specified
                False, # domain_initial_dot
                path, # path
                False, # path_specified
                cookie["secure"], # secure
                cookie["expires"], # expires
                False, # discard
                None, # comment
                None, # comment_url
                {}, # rest
            )
            if not domain in jar_1._cookies:
                jar_1._cookies[domain] = dict()
            if not path in jar_1._cookies[domain]:
                jar_1._cookies[domain][path] = dict()
            jar_1._cookies[domain][path][name] = cookie_1

        jar_1.save(file_path)

        del jar_1
