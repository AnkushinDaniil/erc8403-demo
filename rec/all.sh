#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd $ROOT/rec
./record.sh 2 > take-all.log 2>&1
grep -E "END|Trace|timeout|Error" take-all.log | head -5
cd ..
N=$(.venv/bin/python rec/comp.py rec/raw-2.mkv out/screen-2.mp4 rec/events.json | sed -n 's/.*written \([0-9]*\).*/\1/p')
echo live frames $N
.venv/bin/python rec/timeline.py $N | grep -E "OVER|^TI"
.venv/bin/python rec/render_all.py | tail -6
