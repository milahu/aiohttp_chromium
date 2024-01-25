#!/usr/bin/env python3

# websocket server that returns an infinite stream response
# sending one timestamp per second
# useful for measuring latency of response handlers

"""
python websocket-server.py 2351 &
sleep 2
websocat ws://127.0.0.1:2351/
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
    response = aiohttp.web.WebSocketResponse()
    await response.prepare(request)
    while True:
        t = time.time()
        chunk = f"{t}\n".encode("ascii")
        try:
            await response.send_bytes(chunk)
        except ConnectionResetError:
            return response
        # note: the time between response.write calls
        # will be slightly longer than 1 second
        # instead of sleep, try to read a response
        #await asyncio.sleep(1)
        try:
            ws_message = await response.receive(timeout=1)
            if ws_message.type != aiohttp.web.WSMsgType.CLOSED:
                logger.info(f"ws_message {repr(ws_message.data)}")
        except asyncio.exceptions.TimeoutError:
            pass
        except Exception as e:
            logger.info(f"ws_message {type(e)} {e}")
    await response.write_eof()
    return response



def ws_server():

    logger = logging.getLogger("ws_server")

    # https://docs.aiohttp.org/en/stable/web_reference.html

    # disable info messages, these are too verbose
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

    app = aiohttp.web.Application(
        logger=logger,
    )

    app.add_routes([aiohttp.web.get('/', handle_request)])

    host = "127.0.0.1"
    port = int(sys.argv[1])
    url = f"ws://{host}:{port}/"
    logger.info(f"starting server on {url}")

    aiohttp.web.run_app(
        app,
        host=host,
        port=port,
    )



if __name__ == "__main__":
    ws_server()
