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
        #_chromium_extensions = [
        #    "Ublock", # FIXME slow init
        #],
        cookie_jar = cookie_jar,
    )
    async with aiohttp.ClientSession(**args) as session:
        url = "http://httpbin.org/get" # json response
        url = "https://nowsecure.nl/#relax" # captcha challenge
        # TODO test more captchas https://nopecha.com/demo
        # file download
        # Content-Disposition: attachment; filename="test.json"
        # https://github.com/postmanlabs/httpbin/issues/240
        url = "http://httpbin.org/response-headers?Content-Type=text/plain;%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22test.json%22"
        # FIXME redirect to http 404 page https://www.opensubtitles.org/en/msg-dmca
        url = "https://dl.opensubtitles.org/en/download/sub/6773940"
        print("session.get", url)
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

        if False:

            import _io

            url = "http://httpbin.org/get" # json response

            response = await session.get(url, timeout=2*60)

            response_status = response.status
            response_content = response.content
            response_headers = response.headers

            print("response_status", response_status)
            print("response_content", response_content)
            print("response_content type", type(response_content))
            print("response_headers", response_headers)

            response_content_str_or_bytes = None

            if False:
                pass
            elif type(response_content) in {_io.TextIOWrapper, _io.BufferedReader}:
                # aiohttp_chromium.ClientSession.Response
                response_content_str_or_bytes = response_content.read()
            elif hasattr(response_content, "read"):
                # aiohttp
                response_content_str_or_bytes = await response_content.read()

            print("response_content_str_or_bytes", response_content_str_or_bytes)

            #response_content_str_or_bytes = await response_content.read()

            await response.__aexit__(None, None, None)

        #print("sleep outter"); await asyncio.sleep(2)

    print("saving cookies.txt")
    cookie_jar.save()

asyncio.run(main())
