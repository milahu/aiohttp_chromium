#!/usr/bin/env python3

# this is broken, because dataReceived never has data

"""
    example output:

    requestWillBeSent
    responseReceived
    dataReceived data None
    requestWillBeSent: streamResourceContent data None
    requestWillBeSent
    requestWillBeSent: streamResourceContent data None
    responseReceived
    dataReceived data None
    dataReceived data None

    maybe streamResourceContent is called too late
    after the first dataReceived

    but then should be: streamResourceContent data != None
"""

# based on test-stream-response-3.py

# use Network.streamResourceContent
# for passive observing of requests

import asyncio
import base64
import json
import sys
import time
import os

from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from cdp_socket.exceptions import CDPError

async def main():

    options = webdriver.ChromeOptions()

    options.add_argument("--enable-features=WebContentsForceDark")

    driver = await webdriver.Chrome(options)

    target = None
    base_target = None

    url_by_requestId = dict()

    async def requestWillBeSent(args):
        #print(f"requestWillBeSent {json.dumps(args, indent=2)}")
        url = args["request"]["url"]
        print(f"requestWillBeSent {url}")
        #print("requestWillBeSent", url)
        requestId = args["requestId"]
        url_by_requestId[requestId] = url

        # Network.streamResourceContent
        # https://chromedevtools.github.io/devtools-protocol/tot/Network/
        # more data will be passed in Network.dataReceived events
        _args = {
            "requestId": requestId,
        }
        #print("requestWillBeSent: streamResourceContent")
        # not found -> base_target?
        #data = await target.execute_cdp_cmd("Network.streamResourceContent", args)
        # not found -> driver?
        #data = await base_target.execute_cdp_cmd("Network.streamResourceContent", args)
        # not found
        #target = await driver.current_target
        #data = await target.execute_cdp_cmd("Network.streamResourceContent", args)
        # no effect
        # FIXME Network.streamResourceContent and Network.dataReceived is not working
        # too late?
        # data: bufferedData: Data that has been buffered until streaming is enabled.
        print("driver.execute_cdp_cmd")
        try:
            data = await driver.execute_cdp_cmd("Network.streamResourceContent", _args, timeout=2)
            print(f"requestWillBeSent {url}: driver streamResourceContent data", repr(data))
        except (CDPError, TimeoutError) as e:
            print(f"requestWillBeSent {url}: driver streamResourceContent error", e)
            pass

        print("target.execute_cdp_cmd")
        try:
            data = await target.execute_cdp_cmd("Network.streamResourceContent", _args, timeout=2)
            print(f"requestWillBeSent {url}: target streamResourceContent data", repr(data))
        except (CDPError, TimeoutError) as e:
            print(f"requestWillBeSent {url}: target streamResourceContent error", e)
            pass

        print("base_target.execute_cdp_cmd")
        try:
            data = await base_target.execute_cdp_cmd("Network.streamResourceContent", _args, timeout=2)
            print(f"requestWillBeSent {url}: base_target streamResourceContent data", repr(data))
        except (CDPError, TimeoutError) as e:
            print(f"requestWillBeSent {url}: base_target streamResourceContent error", e)
            pass

        # no: No data found for resource with given identifier
        # this only works in responseReceived
        """
        if data == None:
            _args = {
                "requestId": requestId,
            }
            body = await target.execute_cdp_cmd("Network.getResponseBody", _args)
            body = base64.b64decode(body["body"]) if body["base64Encoded"] else body["body"]
            print(f"requestWillBeSent {url}: getResponseBody", repr(body)[:20])
        """

    async def requestWillBeSentExtraInfo(args):
        #print(f"requestWillBeSentExtraInfo {json.dumps(args, indent=2)}")
        print(f"requestWillBeSentExtraInfo")

    async def responseReceived(args):
        #print(f"responseReceived {json.dumps(args, indent=2)}")
        # TODO better. get target of this response
        nonlocal target
        #print("responseReceived", args)
        status = args["response"]["status"]
        url = args["response"]["url"]
        _type = args["response"]["headers"].get("Content-Type")
        print(f"responseReceived {url}")

        # too late?
        _args = {
            "requestId": args["requestId"],
        }
        data = await driver.execute_cdp_cmd("Network.streamResourceContent", _args, timeout=2)

        # bufferedData: Data that has been buffered until streaming is enabled.
        print(f"responseReceived {url}: streamResourceContent data", repr(data))

        if data == None:
            # fix: No data found for resource with given identifier
            await asyncio.sleep(1)
            _args = {
                "requestId": args["requestId"],
            }
            body = await target.execute_cdp_cmd("Network.getResponseBody", _args)
            body = base64.b64decode(body["body"]) if body["base64Encoded"] else body["body"]
            print(f"responseReceived {url}: getResponseBody", repr(body)[:20])

    # FIXME args["data"] is always missing
    # should be enabled by Network.streamResourceContent
    async def dataReceived(args):
        data = args.get("data")
        requestId = args["requestId"]
        url = url_by_requestId[requestId]
        #print(f"dataReceived {json.dumps(args, indent=2)}")
        print(f"dataReceived {url} data", repr(data))

    async def responseReceivedExtraInfo(args):
        #print(f"responseReceivedExtraInfo {json.dumps(args, indent=2)}")
        print(f"responseReceivedExtraInfo")



    target = await driver.current_target
    base_target = await driver.base_target

    # FIXME getting response body as stream is not working with Network.dataReceived
    # passive observing of requests
    # FIXME Network.streamResourceContent
    # Enables streaming of the response for the given requestId. If enabled, the dataReceived event contains the data that was received during streaming.
    # enable Network events: requestWillBeSent, responseReceived, ...
    args = {
        "maxTotalBufferSize": 1_000_000,  # 1GB
        "maxResourceBufferSize": 1_000_000,
        "maxPostDataSize": 1_000_000
    }

    #await target.execute_cdp_cmd("Network.enable", args)
    await driver.execute_cdp_cmd("Network.enable", args)

    #await target.add_cdp_listener("Network.requestWillBeSent", requestWillBeSent)
    await driver.add_cdp_listener("Network.requestWillBeSent", requestWillBeSent)

    #await target.add_cdp_listener("Network.requestWillBeSentExtraInfo", requestWillBeSentExtraInfo)

    #await target.add_cdp_listener("Network.responseReceived", responseReceived)
    await driver.add_cdp_listener("Network.responseReceived", responseReceived)

    #await target.add_cdp_listener("Network.responseReceivedExtraInfo", responseReceivedExtraInfo)

    await base_target.add_cdp_listener("Network.dataReceived", dataReceived)
    await target.add_cdp_listener("Network.dataReceived", dataReceived)
    await driver.add_cdp_listener("Network.dataReceived", dataReceived)



    url = "https://httpbin.org/get" # json response

    # FIXME got no response for method: "Network.streamResourceContent"
    url = "http://127.0.0.1:5125" # long-polling-http-server.py

    #url = "https://nowsecure.nl/#relax" # captcha challenge
    # TODO test more captchas https://nopecha.com/demo
    # file download
    # Content-Disposition: attachment; filename="test.json"
    # https://github.com/postmanlabs/httpbin/issues/240
    #url = "http://httpbin.org/response-headers?Content-Type=text/plain;%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22test.json%22"

    print("driver.get", url)
    # wait_load=True would return too early on https://nowsecure.nl/
    # which returns status 403 for unsolved captcha
    # and status 200 for solved captcha
    # -> manually wait for page load
    await driver.get(url, wait_load=False)
    #await asyncio.sleep(10)
    await asyncio.sleep(2)
    #print("driver.page_source", (await driver.page_source)[:100])

    """
    # retry
    print("retrying")
    await driver.get(url, wait_load=False)
    await asyncio.sleep(2)
    """

    # TODO wait for page load
    #print("sleep"); await asyncio.sleep(99999)

    await driver.quit()

asyncio.run(main())
