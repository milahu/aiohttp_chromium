#!/bin/sh

exec ./chromium-wrapper.sh \
  --user-data-dir=$PWD/user-data \
  --disable-seccomp-sandbox \
  --single-process \
  "https://httpbin.dev/drip?code=200&numbytes=5&duration=5"
