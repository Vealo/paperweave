#!/bin/sh
set -eu

: "$PW_API_BASE_URL"
: "$PW_API_PORT"
printf 'window.PAPERWEAVE_CONFIG = Object.freeze({ apiBaseUrl: window.location.protocol + "//" + window.location.hostname + ":%s" });\n' \
  "$PW_API_PORT" > /usr/share/nginx/html/runtime-config.js
