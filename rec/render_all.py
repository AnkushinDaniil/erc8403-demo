import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, subprocess, shutil, os
R = f'{ROOT}/'
N = round(json.load(open(R + 'rec/timeline.json'))['TOTAL'] * 30)
shutil.rmtree(R + 'out/fr', ignore_errors=True); os.makedirs(R + 'out/fr')
K = 4
cuts = [N * i // K for i in range(K + 1)]
ps = [subprocess.Popen([R + '.venv/bin/python', R + 'rec/frames.py', R + 'out/fr', str(a), str(b)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for a, b in zip(cuts, cuts[1:])]
for p in ps: print(p.communicate()[0].strip()[-200:])
print("frames", len(os.listdir(R + 'out/fr')), "of", N)
print(subprocess.run([R + '.venv/bin/python', R + 'rec/build.py'], capture_output=True, text=True).stdout[-400:])
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "csv=p=0", R + "out/erc8403-demo.mp4"], capture_output=True, text=True).stdout)
