#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd $ROOT/rec
pkill -f 'xterm -geometry'; sleep 0.3
rm -f gate/*
X="-fa DejaVu\ Sans\ Mono -b 14 -bw 0 +sb"
(DISPLAY=:108 setsid nohup xterm -geometry 58x16+0+0 -fa "DejaVu Sans Mono" -fs 20 -bg '#0d1117' -fg '#e6edf3' -b 14 -bw 0 +sb -e ./t_alice.sh >/dev/null 2>&1 &)
(DISPLAY=:108 setsid nohup xterm -geometry 58x13+0+620 -fa "DejaVu Sans Mono" -fs 20 -bg '#1c0e12' -fg '#f0e6e6' -b 14 -bw 0 +sb -e ./t_thief.sh >/dev/null 2>&1 &)
(DISPLAY=:108 setsid nohup xterm -geometry 78x11+1030+640 -fa "DejaVu Sans Mono" -fs 13 -bg '#0b0e14' -fg '#9da7b3' -b 12 -bw 0 +sb -e ./t_log.sh >/dev/null 2>&1 &)
sleep 1.5
echo terms
