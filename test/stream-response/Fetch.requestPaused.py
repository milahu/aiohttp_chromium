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

    target = await driver.current_target
    base_target = await driver.base_target

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

        # we dont need the raw body any more. encode it to base64
        if type(body) == str:
            body = body.encode("utf8")
        # fix: TypeError: Object of type bytes is not JSON serializable
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

    args = {
        # by default, requestStage == "Request"
        "patterns": [
            {"requestStage": "Request", "urlPattern":"*"},
            {"requestStage": "Response", "urlPattern":"*"},
        ]
    }

    # only for driver.current_target
    await target.execute_cdp_cmd("Fetch.enable", args)
    await target.add_cdp_listener("Fetch.requestPaused", requestPaused)

    """
    # for all targets
    # TODO verify
    await driver.execute_cdp_cmd("Fetch.enable", args)
    await driver.add_cdp_listener("Fetch.requestPaused", requestPaused)
    """

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

    #await asyncio.sleep(10)
    #print("driver.page_source", (await driver.page_source)[:100])

    #print("driver.targets", await driver.targets)

    # TODO wait for page load
    print("sleep"); await asyncio.sleep(99999)

    await driver.quit()

asyncio.run(main())
