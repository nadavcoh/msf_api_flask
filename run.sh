#!/bin/sh
open -a iTerm.app "/usr/local/bin/redis-server"
. venv/bin/activate
flask --debug run --port=2705 --cert=key.crt --key=key.key