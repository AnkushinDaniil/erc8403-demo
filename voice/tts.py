import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, sys, subprocess
sys.path.insert(0, f'{ROOT}/voice')
import edge_tts
from lines import LINES
VOICE = "en-US-AndrewMultilingualNeural"
async def one(k, text):
    c = edge_tts.Communicate(text, VOICE, rate="+6%", boundary="WordBoundary")
    words = []
    with open(f"{ROOT}/voice/{k}.mp3", "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": words.append([ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]])
    d = float(subprocess.check_output(["ffprobe", "-v", "0", "-show_entries", "format=duration", "-of", "csv=p=0", f"{ROOT}/voice/{k}.mp3"]))
    return k, {"text": text, "dur": d, "words": words}
async def main():
    out = dict([await one(k, t) for k, t in LINES])
    json.dump(out, open(f"{ROOT}/voice/voice.json", "w"), indent=1)
    for k, v in out.items(): print(k, round(v["dur"], 2), len(v["words"]), "words")
    print("total", round(sum(v["dur"] for v in out.values()), 1))
asyncio.run(main())
