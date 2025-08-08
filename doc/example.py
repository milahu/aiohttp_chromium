#!/usr/bin/env python3

# fix: ModuleNotFoundError: No module named 'aiohttp_chromium'
import os
import sys
assert os.path.exists("src/aiohttp_chromium/client.py")
sys.path.insert(0, "src")

import asyncio

# no fix
"""
# fix?
# AttributeError: 'coroutine' object has no attribute 'is_displayed'
# <sys>:0: RuntimeWarning: coroutine 'Chrome.find_element' was never awaited
import nest_asyncio
nest_asyncio.apply()
"""

#import aiohttp
import aiohttp_chromium as aiohttp

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

async def main():
    async with aiohttp.ClientSession() as session:
        return await main_inner(session)

async def main_inner(session):

    url = "https://antcpt.com/score_detector/"

    async with session.get(url) as response:

        print(response.status)
        print(await response.text())

        # selenium interface
        # https://www.selenium.dev/documentation/
        # https://stackoverflow.com/questions/59130200/selenium-wait-until-element-is-present-visible-and-interactable
        driver = response._driver

        # parse captcha score. it should be 0.7 or higher
        # browser extensions can cause a lower score -> harder captchas
        # example: "Your score is: 0.7"
        selector = "#app > div > div > div:nth-child(1) > p:nth-child(1) > big"
        wait = WebDriverWait(driver, timeout=10)
        # FIXME AttributeError: 'coroutine' object has no attribute 'is_displayed'
        # RuntimeWarning: coroutine 'Chrome.find_element' was never awaited
        # similar issue:
        # https://github.com/pyppeteer/pyppeteer/issues/179
        elem = await wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
        print(elem, dir(elem))

asyncio.run(main())
