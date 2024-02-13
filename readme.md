# aiohttp_chromium

aiohttp-like interface to chromium

based on [selenium_driverless](https://github.com/kaliiiiiiiiii/Selenium-Driverless) to bypass cloudflare



## status

working prototype



## usage

`aiohttp_chromium` is a drop-in replacement for `aiohttp`

```py
import asyncio

#import aiohttp
import aiohttp_chromium as aiohttp

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://httpbin.org/get') as response:
            print(response.status)
            print(await response.text())

asyncio.run(main())
```

see also

- [aiohttp docs](https://docs.aiohttp.org/en/stable/client.html)
- [test.py](test.py)



## why

handling file downloads with `selenium` is too verbose,
and too complex to integrate into `selenium`,
so this is a wrapper for `selenium`

i wanted a "stupid http client",
so it has the same interface as `aiohttp.client`,
and handling web pages has lower priority,
so the `selenium` interface is hidden in `response._driver`



## examples

- [crx4chrome-scraper](https://github.com/milahu/crx4chrome-scraper)



## known issues



### chromium window is stealing focus

when creating new tabs, or when switching between tabs,
the chromium window is grabbing focus

this is an issue with the window manager

workaround for the KDE plasma desktop:
move the chromium window to a different desktop,
and focus some window

chromium seems to have no
[command line switch](https://peter.sh/experiments/chromium-command-line-switches/)
to disable this focus-grabbing

possible solutions

- run chromium in a LD_PRELOAD wrapper
- binary patching of the chromium executable
- configure the window manager



## todo

- add support for "click to download file" with `async with response._click(elem) as response:` when there is no url for `async with session.get(url, referrer=referrer) as response:`
- add support for streams: request streams, response streams
  - currently, `session.get` only works for "short and small" requests and responses, but not for infinite streams
  - implementing this is non-trivial, because chromium does not expose streams over the [Chrome DevTools Protocol (CDP)](https://chromedevtools.github.io/devtools-protocol/)
  - https://github.com/kaliiiiiiiiii/Selenium-Driverless/issues/123
    - i guess this is very deliberate sabotage, to prevent "abusing" chromium as a generic http client, which is pretty much what we are trying to do here...
  - https://github.com/wkeeling/selenium-wire/issues/656#issuecomment-1848393185
    - sounds like we need either/or: a patched version of chromium, or a dynamic analysis tool like frida to insert hooks into the chromium binary ... to pipe all requests and responses through a local http proxy, for passive tracing and active intercepting of https traffic
    - tracing https traffic with frida
      - https://gaiaslastlaugh.medium.com/frida-as-an-alternative-to-network-tracing-5173cfbd7a0b
      - https://andydavies.me/blog/2019/12/12/capturing-and-decrypting-https-traffic-from-ios-apps/
      - https://stackoverflow.com/questions/46711786/android-hooking-https-traffic-using-frida
      - https://frida.re/docs/frida-trace/
  - https://groups.google.com/g/chrome-debugging-protocol/c/w65z0cMqgvc - Fetch.fulfillRequest and (very) long body
    - there's no streaming support for Fetch network interception
    - there is Fetch.takeResponseBodyAsStream and IO.read, but not Fetch.giveResponseBodyAsStream and IO.write
    - there is Network.takeResponseBodyForInterceptionAsStream and IO.read, but not Network.giveResponseBodyForInterceptionAsStream and IO.write
- graphical interface where the user can solve challenges: captchas, unexpected responses, ...
- integration with captcha solving services
- remove unfree dependencies
  - [selenium_driverless](https://github.com/kaliiiiiiiiii/Selenium-Driverless) - [cc by-nc-sa license](http://creativecommons.org/licenses/by-nc-sa/4.0/)
    - `selenium_driverless` is a high-level wrapper for the [Chrome DevTools Protocol (CDP)](https://chromedevtools.github.io/devtools-protocol/)
    - NOT based on chromedriver binary, because chromedriver is detected by cloudflare
  - see also [Awesome Chrome DevTools # Libraries for driving the protocol (or a layer above)](https://github.com/ChromeDevTools/awesome-chrome-devtools?tab=readme-ov-file#libraries-for-driving-the-protocol-or-a-layer-above)
    - https://github.com/pyppeteer/pyppeteer - 3K stars
    - https://github.com/fake-name/ChromeController - 200 stars
    - https://github.com/chazkii/chromewhip - 120 stars
- `grep -r -w FIXME src/`
- `grep -r -w TODO src/`



## keywords

- web scraper
- chromium
- aiohttp
- web scraping
- asyncio
- bypass cloudflare
- headful scraper
- headful web scraper
- headful chromium
- gui scripting
- headful webscraper
- selenium driverless



## similar projects

- [botasaurus](https://github.com/omkarcloud/botasaurus)
