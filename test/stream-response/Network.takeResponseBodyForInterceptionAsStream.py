#!/usr/bin/env python3

"""
Network.takeResponseBodyForInterceptionAsStream is as good as deprecated,
because Network.requestIntercepted is deprecated, which is needed to get interceptionId
"""

# based on test-modify-request-headers.py
# diff -u test-modify-request-headers.py test-stream-response.py

import asyncio
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
import base64

async def main():

    driver = await webdriver.Chrome()
    #await asyncio.sleep(1)

    target = None
    base_target = None

    interceptionId = None

    async def requestWillBeSent(args):
        #print("requestWillBeSent", args)
        print("requestWillBeSent", args["request"]["url"])

    async def requestWillBeSentExtraInfo(args):
        print("requestWillBeSentExtraInfo", args)

    async def responseReceived(args):
        print("responseReceived", args)
        # TODO better. get target of this response
        nonlocal target
        #print("responseReceived", args)
        print("responseReceived status")
        status = args["response"]["status"]
        print("responseReceived url")
        url = args["response"]["url"]
        print("responseReceived type")
        _type = args["response"]["headers"].get("Content-Type")

        print("responseReceived sleep")
        # TODO better. detect when response data is ready
        # fix: No data found for resource with given identifier
        await asyncio.sleep(1)

        # Network.streamResourceContent
        # https://chromedevtools.github.io/devtools-protocol/tot/Network/

        print("responseReceived body")

        print("Network.takeResponseBodyForInterceptionAsStream")
        args = {
            # TODO?
            "interceptionId": interceptionId,
        }
        stream = await driver.execute_cdp_cmd("Network.takeResponseBodyForInterceptionAsStream", args)
        stream = stream["stream"]
        print("Network.takeResponseBodyForInterceptionAsStream ->", stream)

    # FIXME args["data"] is always missing
    async def dataReceived(args):
        print("dataReceived", args)

    async def responseReceivedExtraInfo(args):
        print("responseReceivedExtraInfo", args)

    async def targetCreated(args):
        print("targetCreated", args)

    async def targetInfoChanged(args):
        #print("targetInfoChanged", args)
        print("targetInfoChanged")

    # Deprecated, use Fetch.requestPaused instead.
    # -> Fetch.enable
    async def requestIntercepted(params):
        nonlocal target

        global interceptionId
        # keyerror: interceptionId
        #interceptionId = args["interceptionId"]

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
        # FIXME Invalid state for continueInterceptedRequest
        await target.execute_cdp_cmd("Network.continueInterceptedRequest", fulfill_params)
        print("requestIntercepted: url", url)

    target = await driver.current_target
    #print("target.id", target.id)

    base_target = await driver.base_target

    # enable Target events
    args = {
        "discover": True,
        #"filter": ...
    }
    await target.execute_cdp_cmd("Target.setDiscoverTargets", args)

    args = {
        "maxTotalBufferSize": 1_000_000,  # 1GB
        "maxResourceBufferSize": 1_000_000,
        "maxPostDataSize": 1_000_000
    }
    #await target.execute_cdp_cmd("Network.enable", args)

    # deprecated in favor of Fetch.enable
    args = {
        "patterns": [{"urlPattern": "*"}],
        #"interceptionStage": "HeadersReceived",
    }
    await target.execute_cdp_cmd("Network.setRequestInterception", args)

    await target.add_cdp_listener("Network.requestIntercepted", requestIntercepted)

    #print("driver.targets", await driver.targets)

    # enable Network events
    args = {
        "maxTotalBufferSize": 1_000_000,  # 1GB
        "maxResourceBufferSize": 1_000_000,
        "maxPostDataSize": 1_000_000
    }
    await target.execute_cdp_cmd("Network.enable", args)

    await target.add_cdp_listener("Network.requestWillBeSent", requestWillBeSent)
    #await target.add_cdp_listener("Network.requestWillBeSentExtraInfo", requestWillBeSentExtraInfo)
    await target.add_cdp_listener("Network.responseReceived", responseReceived)
    #await target.add_cdp_listener("Network.responseReceivedExtraInfo", responseReceivedExtraInfo)



    #await asyncio.sleep(1)

    url = "http://httpbin.org/get" # json response
    #url = "https://nowsecure.nl/#relax" # captcha challenge
    # TODO test more captchas https://nopecha.com/demo
    # file download
    # Content-Disposition: attachment; filename="test.json"
    # https://github.com/postmanlabs/httpbin/issues/240
    #url = "http://httpbin.org/response-headers?Content-Type=text/plain;%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22test.json%22"

    print("driver.get", url)
    await driver.get(url)
    await asyncio.sleep(10)
    print("driver.page_source", (await driver.page_source)[:100])

    #print("driver.targets", await driver.targets)

    """
    print("hit enter to close")
    input()
    """

    await driver.close()

asyncio.run(main())
