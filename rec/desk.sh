#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd $ROOT
pkill -f '[w]eb/serve.py'; pkill -f '[X]vfb :108'; pkill -f '[r]ec/chrome-profile'; sleep 0.5
(setsid nohup ./.venv/bin/python web/serve.py >/dev/null 2>&1 &)
(setsid nohup Xvfb :108 -screen 0 1920x1200x24 >/dev/null 2>&1 &)
sleep 1.5
DISPLAY=:108 xsetroot -solid '#2e425c' 2>/dev/null
rm -rf rec/chrome-profile; mkdir -p rec/chrome-profile
(DISPLAY=:108 setsid nohup ${CHROME:-chromium} --no-sandbox --user-data-dir=$ROOT/rec/chrome-profile --remote-debugging-port=9333 --window-position=1030,0 --window-size=890,600 --test-type --no-first-run --disable-notifications --no-default-browser-check http://127.0.0.1:8700/account/0x00000000000000000000000000000000CAfE8403 >/dev/null 2>&1 &)
sleep 4
