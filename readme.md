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

- graphical interface where the user can solve challenges: captchas, unexpected responses, ...
- integration with captcha solving services
- remove unfree dependencies
  - [selenium_driverless](https://github.com/kaliiiiiiiiii/Selenium-Driverless) - [cc by-nc-sa license](http://creativecommons.org/licenses/by-nc-sa/4.0/)
    - `selenium_driverless` is a high-level wrapper for the [Chrome DevTools Protocol (CDP)](https://chromedevtools.github.io/devtools-protocol/)
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
