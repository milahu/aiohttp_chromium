# aiohttp_chromium

aiohttp-like interface to chromium

aka: headful webscraper



## status

working prototype



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
