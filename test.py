#!/usr/bin/env python3

# https://docs.aiohttp.org/en/stable/client_quickstart.html#make-a-request

import sys

import asyncio

sys.path.append("src")
#import aiohttp_chromium
import aiohttp_chromium as aiohttp

async def main():
    print("aiohttp.ClientSession")
    cookie_jar = aiohttp.MozillaCookieJar("cookies.txt")
    print("loading cookies.txt")
    cookie_jar.load()
    args = dict(
        _chromium_extensions = [
            #"Ublock", # FIXME slow init
        ],
        cookie_jar = cookie_jar,
    )
    async with aiohttp.ClientSession(**args) as session:
        print("session.get")
        url = "http://httpbin.org/get" # json response
        url = "https://nowsecure.nl/#relax" # captcha challenge
        # TODO test more captchas https://nopecha.com/demo
        # file download
        # Content-Disposition: attachment; filename="test.json"
        # https://github.com/postmanlabs/httpbin/issues/240
        url = "http://httpbin.org/response-headers?Content-Type=text/plain;%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22test.json%22"
        async with session.get(url, timeout=2*60) as resp:
            print("resp.status"); print(resp.status)
            print("resp.text"); print((await resp.text())[:200] + " ...")
            # FIXME remove
            #print("sleep inner"); await asyncio.sleep(2)
            """
            print("resp.content"); print(resp.content)
            print("resp.read"); print(await resp.read())
            print("resp.content.read"); print(await resp.content.read())
            """

        #print("sleep outter"); await asyncio.sleep(2)

    print("saving cookies.txt")
    cookie_jar.save()

asyncio.run(main())
