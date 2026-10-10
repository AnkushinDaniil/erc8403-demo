#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd $ROOT/rec
N=${1:-1}
../chain/reset.sh
./desk.sh
./terms.sh
rm -f events.json
ffmpeg -loglevel error -y -f x11grab -draw_mouse 0 -framerate 30 -video_size 1920x1200 -i :108 -c:v libx264 -preset ultrafast -crf 10 -pix_fmt yuv420p raw-$N.mkv &
FF=$!
sleep 1
timeout 400 ../.venv/bin/python take.py > take-$N.log 2>&1
sleep 0.5
kill -INT $FF; wait $FF
cat take-$N.log
ffprobe -v error -show_entries format=duration -of csv=p=0 raw-$N.mkv
[ -e events.json ] && cp events.json ev-$N.json
