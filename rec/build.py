import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, subprocess, sys
R = f'{ROOT}/'
TL = json.load(open(R + 'rec/timeline.json'))
NI = round(TL['TI'] * 30)
NL = round(TL['LIVE'] * 30)
import sys
sys.path.insert(0, R + 'voice')
from lines import LINES
order = [k for k, _ in LINES]
r = subprocess.run([R + '.venv/bin/python', R + 'rec/comp.py', R + 'rec/raw-2.mkv', R + 'out/live.mp4', R + 'rec/events.json', R + 'out/fr', str(NI)], capture_output=True, text=True)
print(r.stdout, r.stderr[-400:])
cmd = ["ffmpeg", "-loglevel", "error", "-y", "-framerate", "30", "-start_number", "0", "-i", R + "out/fr/%05d.jpg", "-i", R + "out/live.mp4",
       "-framerate", "30", "-start_number", str(NI + NL), "-i", R + "out/fr/%05d.jpg"]
for k in order: cmd += ["-i", R + f"voice/{k}.mp3"]
fc = f"[0:v]trim=end_frame={NI},setpts=PTS-STARTPTS,fps=30,format=yuv420p,setsar=1[v0];[1:v]fps=30,format=yuv420p,setsar=1[v1];[2:v]fps=30,format=yuv420p,setsar=1[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v];"
for i, k in enumerate(order): fc += f"[{i + 3}:a]aresample=48000,adelay={int(TL['starts'][k] * 1000)}:all=1[a{i}];"
fc += "".join(f"[a{i}]" for i in range(len(order))) + f"amix=inputs={len(order)}:normalize=0,loudnorm=I=-16:TP=-1.5,apad[m]"
cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[m]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "160k", "-t", "%.3f" % TL['TOTAL'], "-movflags", "+faststart", R + "out/erc8403-demo.mp4"]
print(subprocess.run(cmd, capture_output=True, text=True).stderr[-800:])
