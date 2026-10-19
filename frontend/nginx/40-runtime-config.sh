#!/bin/sh
set -eu

: "${PW_API_BASE_URL:?PW_API_BASE_URL must be supplied from config.toml}"
printf 'window.PAPERWEAVE_CONFIG = Object.freeze({ apiBaseUrl: "%s" });\n' \
  "$PW_API_BASE_URL" > /usr/share/nginx/html/runtime-config.js
