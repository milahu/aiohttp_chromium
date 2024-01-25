#!/usr/bin/env python3

# http server that returns an infinite stream response
# sending one timestamp per second
# useful for measuring latency of response handlers

"""
python long-polling-http-server.py 2351 &
sleep 2
curl http://127.0.0.1:2351/ --no-buffer
"""

import asyncio
import sys
import time
import logging
import time

import aiohttp
import aiohttp.web



logging_level = "INFO"
#logging_level = "DEBUG"

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    level=logging_level,
)

logger = logging.getLogger()



async def handle_request(request):
    headers = {
        "content-type": "application/octet-stream; charset=binary",
        "content-transfer-encoding": "Binary",
        # note: no content-length header
    }
    response = aiohttp.web.StreamResponse(
        headers=headers,
        # note: no body
    )
    await response.prepare(request)
    while True:
        t = time.time()
        chunk = f"{t}\n".encode("ascii")
        try:
            await response.write(chunk)
        except ConnectionResetError:
            return response
        # note: the time between response.write calls
        # will be slightly longer than 1 second
        await asyncio.sleep(1)
    await response.write_eof()
    return response



def http_server():

    logger = logging.getLogger("http_server")

    # https://docs.aiohttp.org/en/stable/web_reference.html

    # disable info messages, these are too verbose
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

    app = aiohttp.web.Application(
        logger=logger,
    )

    app.add_routes([aiohttp.web.get('/', handle_request)])

    host = "127.0.0.1"
    port = int(sys.argv[1])
    url = f"http://{host}:{port}/"
    logger.info(f"starting server on {url}")

    aiohttp.web.run_app(
        app,
        host=host,
        port=port,
    )



if __name__ == "__main__":
    http_server()
