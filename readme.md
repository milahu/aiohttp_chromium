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
        async with session.get('http://httpbin.org/get') as resp:
            print(resp.status)
            print(await resp.text())

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



## known issues



### chromium window is stealing focus

when creating new tabs, or when switching between tabs,
the chromium window is grabbing focus

this is an issue with the window manager

by default (`_headless=False, _prevent_focus_stealing=True`)
this is already fixed in `_enable_prevent_focus_stealing_kde` for the KDE plasma desktop

manual fix on the KDE plasma desktop:
KWin focus stealing prevention:
window titlebar &rarr; rightclick &rarr; more actions &rarr; special settings for this window
&rarr; add property &rarr; prevent unwanted activation &rarr; level: extreme &rarr; apply

example KDE config file `~/.config/kwinrulesrc`

```
[General]
count=1
rules=28ef9b3f-6f35-4fbf-b2c6-b06d0fd959e3

[28ef9b3f-6f35-4fbf-b2c6-b06d0fd959e3]
Description=aiohttp_chromium: prevent focus stealing
clientmachine=localhost
fsplevel=4
fsplevelrule=2
types=1
windowrole=browser
windowrolematch=1
wmclass=chromium-browser \(/run/user/1000/fetch\-subs\-[0-9]{8}T[0-9]{6}\.[0-9]+Z/chromium\-user\-data\) Chromium-browser
wmclasscomplete=true
wmclassmatch=3
```

`/run/user/1000/fetch\-subs\-[0-9]{8}T[0-9]{6}\.[0-9]+Z/chromium\-user\-data`
is a regex for the chromium user-data directory path
which is the `tempdir` argument for `ClientSession`

chromium seems to have no
[command line switch](https://peter.sh/experiments/chromium-command-line-switches/)
to disable this focus-grabbing

possible solutions

- run chromium in a LD_PRELOAD wrapper
- binary patching of the chromium executable
- configure the window manager
  - done for KDE plasma



## todo

- remove tempfiles on session close and on error
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
    - google has hidden the discussion: "You don't have permission to access this content. For access, try contacting the group's owners and managers"
      - see [snapshot](doc/Fetch.fulfillRequest.and.very.long.body.html) from [archive.org 2024-06-23](https://web.archive.org/web/20240623221934/https://groups.google.com/g/chrome-debugging-protocol/c/w65z0cMqgvc)
      - hey google? thanks for reminding us that google is a bunch of fascists, engaging in sabotage and censorship
  - https://issues.chromium.org/issues/332570739 - Streaming body for Fetch.fulfillRequest() CDP API
    - Fetch.fullfillRequest() only provides an option to set the 'body' response as a base64-encoded string. Of course, this does not work well for larger response body. Similar to the streaming takeResponseBodyAsStream(), it would be great if there was a fullfillRequest() option with a stream, fullfillRequestWithStream()
      - Perhaps this could be done by expanding the IO APIs to have a IO.write() option that allows sending a streaming data to the browser. I realize this is probably fairly low-priority, but would make Fetch request interception more efficient, especially when dealing with larger responses/chunked response of unknown size, etc...
    - The feature request makes sense but currently it is a low priority for us.
    - see [snapshot](doc/Streaming.body.for.Fetch.fulfillRequest.CDP.API.332570739.Chromium.html)
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
