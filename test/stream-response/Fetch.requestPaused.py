#!/usr/bin/env python3

# based on test-modify-request-headers.py
# diff -u test-modify-request-headers.py test-stream-response.py

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

    driver = await webdriver.Chrome()
    #await asyncio.sleep(1)

    target = None
    base_target = None

    interceptionId = None

    async def requestWillBeSent(args):
        print(f"requestWillBeSent {json.dumps(args, indent=2)}")
        #print("requestWillBeSent", args["request"]["url"])

    async def requestWillBeSentExtraInfo(args):
        print(f"requestWillBeSentExtraInfo {json.dumps(args, indent=2)}")

    async def responseReceived(args):
        print(f"responseReceived {json.dumps(args, indent=2)}")
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
        """
        args = {
            "requestId": args["requestId"],
        }
        body = await target.execute_cdp_cmd("Network.getResponseBody", args)
        body = base64.b64decode(body["body"]) if body["base64Encoded"] else body["body"]
        print("responseReceived", status, url, _type, repr(body[:20]) + "...")
        """

        # Network.streamResourceContent
        # more data will be passed in Network.dataReceived events
        args = {
            "requestId": args["requestId"],
        }

        # not found -> base_target?
        #data = await target.execute_cdp_cmd("Network.streamResourceContent", args)
        # not found -> driver?
        #data = await base_target.execute_cdp_cmd("Network.streamResourceContent", args)
        #data = await driver.execute_cdp_cmd("Network.streamResourceContent", args)

        print("Network.takeResponseBodyForInterceptionAsStream")
        args = {
            "interceptionId": interceptionId,
        }
        stream = await driver.execute_cdp_cmd("Network.takeResponseBodyForInterceptionAsStream", args)
        stream = stream["stream"]
        print("Network.takeResponseBodyForInterceptionAsStream ->", stream)

    """
    async def requestIntercepted(args):
        print("requestIntercepted")
        global interceptionId
        interceptionId = args["interceptionId"]
    """

    # FIXME args["data"] is always missing
    async def dataReceived(args):
        print(f"dataReceived {json.dumps(args, indent=2)}")

    async def responseReceivedExtraInfo(args):
        print(f"responseReceivedExtraInfo {json.dumps(args, indent=2)}")

    async def targetCreated(args):
        print(f"targetCreated {json.dumps(args, indent=2)}")

    async def targetInfoChanged(args):
        print(f"targetInfoChanged {json.dumps(args, indent=2)}")

    # Deprecated, use Fetch.requestPaused instead.
    # -> Fetch.enable
    async def requestIntercepted(args):
        print(f"requestIntercepted {json.dumps(args, indent=2)}")
        nonlocal target

        global interceptionId
        # keyerror: interceptionId
        #interceptionId = args["interceptionId"]

        print("requestIntercepted", args)
        url = args["request"]["url"]
        _args = {"interceptionId": args['interceptionId']}
        #if args.get('responseStatusCode') in [301, 302, 303, 307, 308]:
        if False:
            # redirected request
            return await target.execute_cdp_cmd("Network.continueInterceptedRequest", _args)
        _args = {"headers":args["request"]["headers"]}
        _args["headers"]["test"] = "Hello World!"
        _args.update(_args)
        await target.execute_cdp_cmd("Network.continueInterceptedRequest", _args)
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

    # deprecated
    """
    args = {
        "patterns": [{"urlPattern": "*"}],
        #"interceptionStage": "HeadersReceived",
    }
    await target.execute_cdp_cmd("Network.setRequestInterception", args)
    await target.add_cdp_listener("Network.requestIntercepted", requestIntercepted)
    """

    #await target.add_cdp_listener("Network.dataReceived", dataReceived)
    await driver.add_cdp_listener("Network.dataReceived", dataReceived)

    #await target.add_cdp_listener("Target.targetCreated", targetCreated)
    #await target.add_cdp_listener("Target.targetInfoChanged", targetInfoChanged)

    await target.add_cdp_listener("Network.requestIntercepted", requestIntercepted)

    #print("driver.targets", await driver.targets)

    # no. getting response body as stream is not working with Network.dataReceived
    # FIXME Network.streamResourceContent
    # Enables streaming of the response for the given requestId. If enabled, the dataReceived event contains the data that was received during streaming.
    """
    # enable Network events: requestWillBeSent, responseReceived, ...
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
    """

    async def requestPaused(args):
        #print(f"requestPaused {json.dumps(args, indent=2)}")
        url = args["request"]["url"]
        responseStatusCode = args.get("responseStatusCode")
        print(f"requestPaused: status {responseStatusCode} from url {url}")
        _args = {"requestId": args['requestId']}
        if responseStatusCode in [301, 302, 303, 307, 308]:
            print(f"requestPaused handling redirect")
            return await target.execute_cdp_cmd("Fetch.continueResponse", _args)

        # fix: Can only get response body on requests captured after headers received.
        # fix: The request must be paused in the HeadersReceived stage
        if not "responseHeaders" in args:
            # request is before the "HeadersReceived" stage
            print(f"requestPaused: headers not received -> Fetch.continueResponse")
            return await target.execute_cdp_cmd("Fetch.continueResponse", _args)

        # headers received. now we can get the response body
        print(f"requestPaused: headers received -> getting the response body")
        #print(f"requestPaused {json.dumps(args, indent=2)}")

        # no. this requires interceptionId
        #stream = await driver.execute_cdp_cmd("Network.takeResponseBodyForInterceptionAsStream", _args)

        # no: websockets.exceptions.ConnectionClosedError
        #stream = await target.execute_cdp_cmd("Fetch.takeResponseBodyAsStream", _args)
        # fix: target -> driver
        stream = await driver.execute_cdp_cmd("Fetch.takeResponseBodyAsStream", _args)

        stream_handle = stream["stream"]
        # stream_handle is just a number
        #print(f"requestPaused: stream", stream)

        # TODO implement aiohttp.streams.StreamReader
        # dont store the whole response in memory
        # return a reader, and the consumer calls reader.iter_any()
        # to read chunks of the response until EOF
        # async with get_reader() as reader:
        #     async for slice in reader.iter_any():
        #         print(slice)
        data_eof = False
        body = None
        while data_eof == False:
            _args = {
                "handle": stream_handle,
                # error: Read offset is specificed for a stream that does not support random access
                #"offset": idx,
                #"size": 100,
            }
            data = await target.execute_cdp_cmd("IO.read", _args)
            # the EOF event is passed in a separate read with data == ""
            data_eof = data["eof"]
            # base64Encoded
            data = base64.b64decode(data["data"]) if data["base64Encoded"] else data["data"]
            # data can be str or bytes
            if body == None:
                if type(data) == str:
                    body = ""
                else:
                    body = b""
            # empty data is always passed as empty string
            # fix: TypeError: can't concat str to bytes
            if len(data) > 0:
                print(f"requestPaused: data", len(data), repr(data[:100]))
                body += data
            if data_eof:
                print(f"requestPaused: eof")

        # no: Unable to continue request as is after body is taken
        """
        _args = {"requestId": args['requestId']}
        await target.execute_cdp_cmd("Fetch.continueResponse", _args)
        return
        """

        # we dont need the raw body any more. encode it to base64
        if type(body) == str:
            body = body.encode("utf8")

        # test: size limit of body
        # https://groups.google.com/g/chrome-debugging-protocol/c/w65z0cMqgvc
        # all response overrides are inherently limited by whatever fits in a single CDP message.
        # this seems to be limited only by RAM, and by CDP timeouts
        """
        #body = os.urandom(10_000)
        body = b"0" * 1_000_000_000
        if False:
            body = b""
            for i in range(1000):
                body += b"0" * 1_000
                body += (f" len = {i*1_000:e} ").encode("ascii")
        for header in args["responseHeaders"]:
            if header["name"] == "Content-Type":
                header["value"] = "application/octet-stream; charset=binary"
            if header["name"] == "Content-Length":
                header["value"] = str(len(body))
        args["responseHeaders"].append({
            "name": "Content-Disposition",
            "value": 'attachment; filename="blob.bin"',
        })
        """

        # return empty response
        # turn file download into empty page
        # no. file downloads should not leave the current page
        # instead of Fetch.fulfillRequest, use Fetch.failRequest
        """
        requestId = args["requestId"]
        body = (f"ok request {requestId}").encode("utf8")
        for header in args["responseHeaders"]:
            if header["name"] == "Content-Type":
                header["value"] = "text/plain; charset=utf8"
            if header["name"] == "Content-Length":
                header["value"] = str(len(body))
            if header["name"] == "Content-Disposition":
                header["value"] = "inline"
        """

        # dont send response to chromium
        """
        _args = {
            "requestId": args['requestId'],
            # Failed, Aborted, TimedOut, AccessDenied,
            # ConnectionClosed, ConnectionReset, ConnectionRefused, ConnectionAborted, ConnectionFailed,
            # NameNotResolved, InternetDisconnected, AddressUnreachable, BlockedByClient, BlockedByResponse
            "errorReason": "Aborted",
        }
        await target.execute_cdp_cmd("Fetch.failRequest", _args)
        return
        """

        body = base64.b64encode(body).decode("ascii")
        _args = {
            "requestId": args['requestId'],
            "responseCode": args["responseStatusCode"],
            # fix: Please unblock challenges.cloudflare.com to proceed.
            "responseHeaders": args["responseHeaders"],
            "body": body,
        }
        if args["responseStatusText"] != "":
            # empty string throws "Invalid http status code or phrase"
            _args["responsePhrase"] = args["responseStatusText"]

        # FIXME stream
        # how does this work with an infinite-size body?
        # Fetch.continueResponse accepts no data
        # https://groups.google.com/g/chrome-debugging-protocol/c/w65z0cMqgvc
        # Unfortunately, there's no streaming support for Fetch network interception at the moment,
        # so all response overrides are inherently limited by whatever fits in a single CDP message.
        await target.execute_cdp_cmd("Fetch.fulfillRequest", _args)

        # ok, this works, but only for small non-stream responses
        """
        body = await target.execute_cdp_cmd("Fetch.getResponseBody", _args, timeout=1)
        body = base64.b64decode(body["body"]) if body["base64Encoded"] else body["body"]
        print(f"requestPaused: body", body[:100])

        # ?
        # no: This check is taking longer than expected. Check your Internet connection and refresh the page if the issue persists.
        #return await target.execute_cdp_cmd("Fetch.continueResponse", _args)

        body = base64.b64encode(body).decode("ascii")
        _args = {
            "requestId": args['requestId'],
            "responseCode": args["responseStatusCode"],
            # fix: Please unblock challenges.cloudflare.com to proceed.
            "responseHeaders": args["responseHeaders"],
            "body": body,
        }
        await target.execute_cdp_cmd("Fetch.fulfillRequest", _args)
        """

        """
        try:
            body = await target.execute_cdp_cmd("Fetch.getResponseBody", _args, timeout=1)
        except CDPError as e:
            if e.code == -32000 and e.message == 'Can only get response body on requests captured after headers received.':
                #print(args, "\n", file=sys.stderr)
                #traceback.print_exc()
                print(f"requestPaused: headers not received -> Fetch.continueResponse")
                await target.execute_cdp_cmd("Fetch.continueResponse", _args)
            else:
                raise e
        else:
            start = time.monotonic()
            body_decoded = base64.b64decode(body['body'])
            # modify body here
            body_modified = base64.b64encode(body_decoded).decode("ascii")
            _args = {"responseCode": 200, "body": body_modified}
            _args.update(_args)
            _time = time.monotonic() - start
            if _time > 0.01:
                logger_print(f"decoding took long: {_time} s")
            await target.execute_cdp_cmd("Fetch.fulfillRequest", _args)
            logger_print("Mocked response", url)
        """

    args = {
        # by default, requestStage == "Request"
        "patterns": [
            {"requestStage": "Request", "urlPattern":"*"},
            {"requestStage": "Response", "urlPattern":"*"},
        ]
    }
    await target.execute_cdp_cmd("Fetch.enable", args)
    await target.add_cdp_listener("Fetch.requestPaused", requestPaused)

    #await asyncio.sleep(1)

    #url = "http://httpbin.org/get" # json response
    #url = "https://nowsecure.nl/#relax" # captcha challenge
    # TODO test more captchas https://nopecha.com/demo
    # file download
    # Content-Disposition: attachment; filename="test.json"
    # https://github.com/postmanlabs/httpbin/issues/240
    url = "http://httpbin.org/response-headers?Content-Type=text/plain;%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22test.json%22"

    print("driver.get", url)
    # wait_load=True would return too early on https://nowsecure.nl/
    # which returns status 403 for unsolved captcha
    # and status 200 for solved captcha
    # -> manually wait for page load
    await driver.get(url, wait_load=False)
    await asyncio.sleep(10)
    print("driver.page_source", (await driver.page_source)[:100])

    #print("driver.targets", await driver.targets)

    # TODO wait for page load
    print("sleep"); await asyncio.sleep(99999)

    await driver.quit()

asyncio.run(main())
